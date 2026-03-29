import asyncio
from app.qa.llm_qa import LLMQAModule
from app.models.schemas import DocumentChunk
from app.models.schemas import DocumentMetadata
from app.qa.classifier import QueryAnalysis, QueryType

m = LLMQAModule()
c = DocumentChunk(
    content="Agrobank daromadi 2023 yilda 5 trln so'mni tashkil etdi.", 
    chunk_id="1", 
    metadata=DocumentMetadata(file_name="test.pdf", file_path="/fake"),
    source_label="test.pdf p.1"
)
a = QueryAnalysis(query_type=QueryType.TEXTUAL, is_numeric=True, is_table_based=False, is_multi_hop=False, target_metric='revenue', target_year=2023, target_company='Agrobank', confidence=0.9)

async def run():
    try:
        ans, conf = await m.answer('Agrobank daromadlari', [c], a)
        print(f'Ans: {ans}, Conf: {conf}')
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(run())
