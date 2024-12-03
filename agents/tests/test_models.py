
from agents.models import *
from agents.openai_api import LLMFactory
from companies.models import Company
from django.test import TestCase


class TestModels(TestCase):
    def setUp(self):

        self.bloktopia = LLMFactory("Bloktopia")

        with open("resources/bloktopia_about.txt") as content:
            self.bloktopia.save_rag_context_to_model("Bloktopia", [content.read()])

        self.test_context = RAGContext.objects.get(name="Bloktopia")

    def test_rag_context(self):
        self.assertIn("content", self.test_context.documents[0])
        self.assertIn("the new roadmap", self.test_context.documents[0]["content"])

    def test_summarize_documents(self):
        document_json = self.test_context.documents[0]
        summarized = self.bloktopia.summarize_document(document_json)
        # print(summarized["summary"])



