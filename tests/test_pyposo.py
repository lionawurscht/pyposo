from unittest import TestCase
from pyposo import Document, Emph, Strong, Paragraph, Title, Section


class TestPyposo(TestCase):
    @classmethod
    def setUp(self):
        pass

    def test_emph(self):
        self.assertEqual(
            Emph("This is emphasized").dump(), "*This is emphasized*"
        )

    def test_strong(self):
        self.assertEqual(Strong("This is strong").dump(), "**This is strong**")

    def test_paragraph_in_doc(self):
        doc = Document()
        doc.append(Paragraph("This is a paragraph."))
        self.assertEqual(doc.dump(), "This is a paragraph.")

    def test_paragraph(self):
        paragraph = Paragraph("This is a paragraph.")

        self.assertEqual(paragraph.dump(), "This is a paragraph.")

    def test_complicated_document(self):
        doc = Document()
        doc.append(Title("This is a title"))
        doc.append(Paragraph("This comes before the first section."))
        with doc.create(Section("Section")):
            doc.append(
                Paragraph("This is the first paragraph in my first section.")
            )

        expected = "=================\n This is a title \n=================\n\nThis comes before the first section.\n\nSection\n=======\n\nThis is the first paragraph in my first section."

        self.assertEqual(
            doc.dump(),
            expected,
        )
