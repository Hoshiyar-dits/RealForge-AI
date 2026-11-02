class KnowledgeRepository():
    def add(self, chunks, ids):
        # TODO: store the chunks in the vector store
        pass

    def delete_by_document(self, document_id: int):
        # TODO: delete the chunks of one document
        pass

    def delete_by_product(self, product_id: int):
        # TODO: delete the chunks of every document of a product
        pass

    def search(self, query: str, k: int, doc_types: list = None, product_id: int = None):
        # TODO: return the k chunks closest in meaning to the query
        return []
