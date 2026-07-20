"""PubMed API fetcher module."""

import requests
from datetime import datetime
from typing import List
from scripts.models import Paper
from scripts.config import TARGET_KEYWORDS, PUBMED_EMAIL


def fetch_pubmed_papers(days_back: int = 7, max_results: int = 50) -> List[Paper]:
    """PubMed API から最新論文取得"""
    keywords = [
        "hypertension", "blood pressure", "sarcopenia", "cognitive decline", "dementia",
        "type 2 diabetes", "osteoporosis", "frailty", "sleep", "insomnia",
        "gut microbiome", "aging", "older adults", "exercise",
        "protein", "blood pressure", "glucose", "osteoporosis"
    ]
    
    query = " OR ".join([f'"{k}"' for k in keywords])
    query += f' AND ("last {days_back} days"[dp])'
    query += " AND (humans[MeSH Terms])"
    query += " AND (clinical trial[pt] OR meta-analysis[pt] OR guideline[pt] OR review[pt])"
    
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json",
        "email": PUBMED_EMAIL,
        "sort": "relevance"
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        ids = response.json().get("esearchresult", {}).get("idlist", [])
        
        if not ids:
            return []
        
        fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(ids),
            "retmode": "xml",
            "email": PUBMED_EMAIL
        }
        
        fetch_response = requests.get(fetch_url, params=fetch_params, timeout=60)
        fetch_response.raise_for_status()
        
        return parse_pubmed_xml(fetch_response.text)
        
    except Exception as e:
        print(f"PubMed fetch error: {e}")
        return []


def parse_pubmed_xml(xml_text: str) -> List[Paper]:
    """PubMed XML パース"""
    from xml.etree import ElementTree as ET
    
    root = ET.fromstring(xml_text)
    papers = []
    
    for article in root.findall(".//PubmedArticle"):
        try:
            pmid = article.findtext(".//PMID")
            title = article.findtext(".//ArticleTitle", "")
            abstract = article.findtext(".//Abstract/AbstractText", "")
            
            journal_elem = article.find(".//Journal")
            journal = journal_elem.findtext("Title", "") if journal_elem is not None else ""
            
            pub_date_elem = article.find(".//PubDate")
            if pub_date_elem is not None:
                year = pub_date_elem.findtext("Year", "")
                month = pub_date_elem.findtext("Month", "")
                day = pub_date_elem.findtext("Day", "")
                pub_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}" if year else ""
            else:
                pub_date = ""
            
            doi = ""
            for id_elem in article.findall(".//ArticleId"):
                if id_elem.get("IdType") == "doi":
                    doi = id_elem.text
                    break
            
            mesh_terms = []
            for mesh in article.findall(".//MeshHeading/DescriptorName"):
                if mesh.text:
                    mesh_terms.append(mesh.text.lower())
            
            papers.append(Paper(
                title=title,
                abstract=abstract,
                authors=[],
                journal=journal,
                pub_date=pub_date,
                doi=doi,
                url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                tags=mesh_terms
            ))
        except Exception as e:
            print(f"Parse error: {e}")
            continue
    
    return papers