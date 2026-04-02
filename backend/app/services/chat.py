import httpx
import logging
from typing import List, Dict, Any
from app.core.config import settings
from app.services.document import search_document_chunks_hybrid
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.chat import ChatMessage

logger = logging.getLogger(__name__)

class ChatService:
    """
    Service for orchestrating Retrieval-Augmented Generation (RAG).
    
    This service:
    1. Searches for relevant chunks using hybrid search.
    2. Formats the chunks into a context string.
    3. Prompts an LLM (via Ollama) to answer the user query based on the context.
    """
    
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.LLM_MODEL
        self.history_limit = settings.CHAT_HISTORY_LIMIT

    async def rephrase_query(self, query: str, history: List[ChatMessage]) -> str:
        """
        Rephrase a user query based on conversation history into a standalone search query.
        """
        if not history:
            return query

        # Filter and limit history
        recent_history = history[-self.history_limit:]
        
        history_str = "\n".join([f"{msg.role}: {msg.content}" for msg in recent_history])
        
        rephrase_prompt = f"""Dato il seguente storico della conversazione e l'ultima domanda dell'utente, 
riscrivi la domanda in una query di ricerca stand-alone ed efficace per un sistema RAG.
La query deve essere concisa, in italiano, e contenere tutti i termini necessari per la ricerca senza riferimenti pronominali ambigui.
Restituisci SOLO la query, senza introduzioni o spiegazioni.

### STORICO CONVERSAZIONE:
{history_str}

### ULTIMA DOMANDA:
{query}

### QUERY DI RICERCA:"""

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": rephrase_prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.0,  # Deterministic for rephrasing
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    rephrased = result.get("response", query).strip()
                    logger.info(f"Rephrased query: '{query}' -> '{rephrased}'")
                    return rephrased if rephrased else query
                
                logger.warning(f"Ollama rephrase failed: {response.text}")
                return query
        except Exception as e:
            logger.error(f"Error in rephrase_query: {e}")
            return query
    async def ask_question(
        self, 
        db: AsyncSession, 
        query: str, 
        history: List[ChatMessage] = None,
        limit: int = 5, 
        min_score: float = 0.1
    ) -> Dict[str, Any]:
        """
        Ask a question based on retrieved document context.
        """
        # 0. QUERY TRANSFORMATION: Rephrase based on history if needed
        search_query = query
        if history:
            search_query = await self.rephrase_query(query, history)

        # 1. RETRIEVAL: Get relevant chunks using Hybrid Search
        chunks = await search_document_chunks_hybrid(
            db=db, 
            query=search_query, 
            limit=limit, 
            min_score=min_score
        )
        
        if not chunks:
            return {
                "answer": "Non ho trovato informazioni rilevanti nei documenti caricati per rispondere a questa domanda.",
                "context_used": [],
                "model": self.model
            }

        # 2. FORMATTING: Create the context string for the prompt
        context_parts = []
        context_metadata = []
        
        for i, chunk in enumerate(chunks):
            title = chunk.get("document_title", "Unknown Document")
            page = chunk.get("page_number", "?")
            content = chunk.get("content", "").strip()
            
            # Format for the LLM to see
            context_parts.append(f"[Fonte {i+1}: {title}, Pagina {page}]\n{content}")
            
            # Store for the response schema
            context_metadata.append({
                "content": content,
                "document_title": title,
                "page_number": chunk.get("page_number"),
                "score": float(chunk.get("score", 0.0))
            })

        context_str = "\n\n---\n\n".join(context_parts)

        # 3. PROMPTING: Construct the RAG prompt
        system_prompt = (
            "Sei un assistente AI esperto di VerbumLab. Il tuo compito è rispondere alle domande utilizzando ESCLUSIVAMENTE "
            "il contesto fornito qui sotto. Se la risposta non è presente nel contesto, dichiara onestamente che non lo sai. "
            "Cita sempre le tue fonti includendo il titolo del documento e il numero di pagina, ad esempio: "
            "'Secondo il documento [Titolo] a pagina [X]...'. Rispondi sempre in italiano."
        )

        history_context = ""
        if history:
            recent_history = history[-self.history_limit:]
            h_str = "\n".join([f"{msg.role}: {msg.content}" for msg in recent_history])
            history_context = f"\n### STORICO CONVERSAZIONE RECENTE:\n{h_str}\n"
        
        full_prompt = f"""{system_prompt}

### CONTESTO:
{context_str}
{history_context}
### DOMANDA:
{query}

### RISPOSTA:"""

        # 4. GENERATION: Call Ollama API
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": full_prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.2, # Low temperature for factual RAG
                            "top_p": 0.9
                        }
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Ollama generation failed: {response.text}")
                    raise Exception("Errore durante la generazione della risposta AI.")
                
                result = response.json()
                answer = result.get("response", "Nessuna risposta generata.")

                return {
                    "answer": answer,
                    "context_used": context_metadata,
                    "model": self.model
                }

        except Exception as e:
            logger.error(f"Error in ChatService.ask_question: {e}")
            raise

chat_service = ChatService()
