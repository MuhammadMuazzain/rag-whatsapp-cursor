try:
    from rag import RAGEngine
    rag_engine = RAGEngine()
    print('✅ RAG initialized successfully!')
except Exception as e:
    print(f'❌ Error initializing RAG: {e}')