
from agents.models import *
from agents.openai_api import LLMFactory
from companies.models import Company
from django.test import TestCase


class TestModels(TestCase):
    def setUp(self):

        self.bloktopia = LLMFactory("Bloktopia")

        with open("resources/bloktopia_about.txt") as content:

            self.bloktopia.save_rag_context_to_model("Bloktopia", [content.read()])

    def test_rag_context(self):
        context = RAGContext.objects.get(name="Bloktopia")
        self.assertIn("content", context.documents[0])
        self.assertIn("the new roadmap", context.documents[0]["content"])


    def test_summarize_documents(self):
        pass


