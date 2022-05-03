from iiif_prezi.factory import ManifestFactory, Sequence, Canvas, Image, Annotation
from presentation_api.models import Article, Page

class ManifestFactoryExtended(ManifestFactory):
    def set_base_uri(self, base_url: str, article_id : str):
        self.set_base_prezi_uri(f'{base_url}/{article_id}')

    def create_manifest(self, article: Article) :
        manifest = self.manifest(label="journal.volume")
        manifest.description = 'journal.description'
        manifest.add_sequence(self.create_sequence(article))
        return manifest

    def create_sequence(self, article : Article):
        sequence : Sequence = self.sequence()
        for page in article.pages:
            sequence.add_canvas(self.create_canvas(page))

        return sequence

    def create_canvas(self, page: Page):
        canvas : Canvas = self.canvas(ident=str(page.id), label=page.label)
        canvas.height = page.height
        canvas.width = page.width
        annotation = self.create_image_annotation(page)
        annotation.on = canvas.id
        canvas.add_annotation(annotation)

        return canvas

    def create_image_annotation(self, page: Page):
        annotation : Annotation = self.annotation(ident=str(page.id))
        image : Image = annotation.image(ident=page.name, label=page.label, iiif=True)
        image.format = page.format
        image.height = page.height
        image.width = page.width

        return annotation
