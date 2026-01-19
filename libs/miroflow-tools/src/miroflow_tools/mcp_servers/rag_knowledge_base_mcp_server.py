# Copyright (c) 2025 MiroMind
# This source code is licensed under the MIT License.

"""
RAG Knowledge Base MCP Server

Provides tools for querying RAG (Retrieval-Augmented Generation) knowledge bases.
Supports vector search, document retrieval, and collection management.
"""

import os
import json
import logging
from typing import Dict, Any

import httpx
from mcp.server.fastmcp import FastMCP

# Configure logging
logger = logging.getLogger("miroflow")

# RAG API configuration from environment
RAG_API_URL = os.environ.get("RAG_API_URL", "http://localhost:8000")
RAG_API_KEY = os.environ.get("RAG_API_KEY", "")

# Initialize FastMCP server
mcp = FastMCP("rag_knowledge_base")


@mcp.tool()
async def search_knowledge_base(
    query: str,
    collection_name: str = "default",
    top_k: int = 5,
    score_threshold: float = 0.7
) -> str:
    """
    Search the RAG knowledge base for relevant documents using vector similarity.
    
    Use this tool when you need to retrieve information from internal knowledge bases,
    company documents, product manuals, or any other private data sources.
    
    Args:
        query (str): The search query - describe what information you're looking for
        collection_name (str): Name of the knowledge base collection to search (default: "default")
        top_k (int): Maximum number of results to return (default: 5, max: 20)
        score_threshold (float): Minimum relevance score 0-1 (default: 0.7, higher = more relevant)
    
    Returns:
        str: JSON string containing:
            - success (bool): Whether the search was successful
            - query (str): The original query
            - collection (str): Collection that was searched
            - results (list): List of relevant documents with content and metadata
            - count (int): Number of results returned
    
    Example:
        search_knowledge_base(
            query="产品保修政策",
            collection_name="company_policies",
            top_k=3
        )
    """
    # Validate inputs
    if not query or not query.strip():
        return json.dumps({
            "success": False,
            "error": "Query cannot be empty",
            "query": query
        }, ensure_ascii=False)
    
    # Validate top_k
    top_k = min(max(1, top_k), 20)  # Clamp between 1 and 20
    
    # Validate score_threshold
    score_threshold = min(max(0.0, score_threshold), 1.0)  # Clamp between 0 and 1
    
    logger.info(f"RAG Search: query='{query}', collection='{collection_name}', top_k={top_k}")
    
    try:
        # Retry configuration
        retry_delays = [1, 2, 4]
        
        for attempt, delay in enumerate(retry_delays, 1):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{RAG_API_URL}/api/search",
                        headers={
                            "Authorization": f"Bearer {RAG_API_KEY}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "query": query,
                            "collection_name": collection_name,
                            "top_k": top_k,
                            "score_threshold": score_threshold
                        },
                        timeout=httpx.Timeout(None, connect=10, read=30)
                    )
                    
                    response.raise_for_status()
                    break  # Success, exit retry loop
                    
            except httpx.TimeoutException as e:
                if attempt < len(retry_delays):
                    logger.warning(f"RAG Search timeout, retry in {delay}s (attempt {attempt})")
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error("RAG Search timeout after retries")
                    raise e
                    
            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                
                # Retryable errors: 5xx, 408, 429
                if status_code >= 500 or status_code in [408, 429]:
                    if attempt < len(retry_delays):
                        logger.warning(f"RAG Search HTTP {status_code}, retry in {delay}s")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        logger.error(f"RAG Search HTTP {status_code} after retries")
                        raise e
                else:
                    # Non-retryable errors: 4xx (except 408, 429)
                    logger.error(f"RAG Search HTTP {status_code} (non-retryable)")
                    raise e
        
        # Parse response
        result_data = response.json()
        documents = result_data.get("documents", [])
        
        logger.info(f"RAG Search success: {len(documents)} results")
        
        return json.dumps({
            "success": True,
            "query": query,
            "collection": collection_name,
            "results": documents,
            "count": len(documents)
        }, ensure_ascii=False)
        
    except Exception as e:
        error_msg = f"RAG Search error: {str(e)}"
        logger.error(error_msg)
        
        return json.dumps({
            "success": False,
            "error": str(e),
            "query": query,
            "collection": collection_name
        }, ensure_ascii=False)


@mcp.tool()
async def get_document(
    document_id: str,
    collection_name: str = "default"
) -> str:
    """
    Retrieve a specific document by its ID from the knowledge base.
    
    Use this tool when you need the full content of a specific document,
    usually after finding its ID through search_knowledge_base.
    
    Args:
        document_id (str): Unique identifier of the document
        collection_name (str): Name of the knowledge base collection (default: "default")
    
    Returns:
        str: JSON string containing:
            - success (bool): Whether the retrieval was successful
            - document (dict): Full document content and metadata
            - error (str): Error message if failed
    """
    if not document_id or not document_id.strip():
        return json.dumps({
            "success": False,
            "error": "Document ID cannot be empty"
        }, ensure_ascii=False)
    
    logger.info(f"RAG Get Document: id='{document_id}', collection='{collection_name}'")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{RAG_API_URL}/api/document/{document_id}",
                headers={"Authorization": f"Bearer {RAG_API_KEY}"},
                params={"collection": collection_name},
                timeout=httpx.Timeout(None, connect=10, read=30)
            )
            
            response.raise_for_status()
            document = response.json()
            
            logger.info(f"RAG Get Document success: {document_id}")
            
            return json.dumps({
                "success": True,
                "document": document
            }, ensure_ascii=False)
            
    except Exception as e:
        error_msg = f"RAG Get Document error: {str(e)}"
        logger.error(error_msg)
        
        return json.dumps({
            "success": False,
            "error": str(e),
            "document_id": document_id
        }, ensure_ascii=False)


@mcp.tool()
async def list_collections() -> str:
    """
    List all available knowledge base collections.
    
    Use this tool to discover what knowledge bases are available for querying.
    
    Returns:
        str: JSON string containing:
            - success (bool): Whether the operation was successful
            - collections (list): List of available collections with metadata
            - error (str): Error message if failed
    """
    logger.info("RAG List Collections")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{RAG_API_URL}/api/collections",
                headers={"Authorization": f"Bearer {RAG_API_KEY}"},
                timeout=httpx.Timeout(None, connect=10, read=10)
            )
            
            response.raise_for_status()
            collections_data = response.json()
            
            collections = collections_data.get("collections", [])
            logger.info(f"RAG List Collections success: {len(collections)} collections")
            
            return json.dumps({
                "success": True,
                "collections": collections
            }, ensure_ascii=False)
            
    except Exception as e:
        error_msg = f"RAG List Collections error: {str(e)}"
        logger.error(error_msg)
        
        return json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False)


if __name__ == "__main__":
    # Run the MCP server
    import asyncio
    mcp.run(transport="stdio")
