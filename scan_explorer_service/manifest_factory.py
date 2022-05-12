from iiif_prezi.factory import ManifestFactory, Sequence, Canvas, Image, Annotation, Manifest
from scan_explorer_service.models import Article, Page


class ManifestFactoryExtended(ManifestFactory):
    """ Extended manifest factory.

    Extension of the iiif_prezi manifest factory with helper 
    functions used to create manifest objects from model.
    """

    def create_manifest(self, article: Article):
        manifest = self.manifest(
            ident=f'{article.id}/manifest.json', label="journal.volume")
        manifest.description = 'journal.description'
        manifest.add_sequence(self.create_sequence(article))
        return manifest

    def create_sequence(self, article: Article):
        sequence: Sequence = self.sequence()
        for page in article.pages:
            sequence.add_canvas(self.create_canvas(page))

        return sequence

    def create_canvas(self, page: Page):
        canvas: Canvas = self.canvas(ident=str(page.id), label=page.label)
        canvas.height = page.height
        canvas.width = page.width
        annotation = self.create_image_annotation(page)
        annotation.on = canvas.id
        canvas.add_annotation(annotation)

        return canvas

    def create_image_annotation(self, page: Page):
        annotation: Annotation = self.annotation(ident=str(page.id))
        image: Image = annotation.image(
            ident=page.image_path, label=page.label, iiif=True)
        image.format = page.format
        image.height = page.height
        image.width = page.width

        return annotation

    def add_search_service(self, manifest: Manifest, search_url: str):
        context = 'http://iiif.io/api/search/1/context.json'
        profile = 'http://iiif.io/api/search/1/search'
        
        manifest.add_service(ident=search_url, context=context, profile=profile)
