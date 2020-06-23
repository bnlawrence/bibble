import unittest, os
import bibble


class TestBibLatex(unittest.TestCase):
    """ Test execution for specific biblatex exported by Zotero """

    def setUp(self):
        """ Mimic some of the Click Functionality"""
        self.template = open("publications.tmpl", 'r')
        self.output = open("temp.html", "w")

    def test_runner(self):
        """
        Test a decent sized database, with some pathological examples
        includeing inproceedings without booktitle and an incollection
        """
        self.bibfile = open("merge1.bib", "r")
        output = bibble.bibmain(self.bibfile, self.template, None)
        self.output.write(output)

    def test_biblatex(self):
        """
        (1) Dates handled differently in better_biblatex exported by zotero.
        (2) Journal titles handled differently
        """
        self.bibfile = open("example_better_biblatex.bib", 'r')
        output = bibble.bibmain(self.bibfile, self.template, None)
        self.output.write(output)

    def test_doi(self):
        """ Test we can handle a DOI output. This is a standard, not biblatex entry"""
        #  All we want to do here is avoid an error
        self.bibfile = open("example_with_doi.bib",'r')
        output = bibble.bibmain(self.bibfile, self.template, None)
        self.output.write(output)

    def test_unpublished(self):
        """ Want sensible outcomes for unpublished work"""
        self.bibfile = open("example_unpublished.bib","r")
        output = bibble.bibmain(self.bibfile, self.template, None)
        self.output.write(output)

    def tearDown(self, delete=True):
        self.output.close()
        self.template.close()
        self.bibfile.close()
        if delete and os.path.exists("temp.html"):
            os.remove("temp.html")


if __name__ == "__main__":
    unittest.main()

