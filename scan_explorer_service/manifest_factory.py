from typing import Dict, Iterable
from iiif_prezi.factory import ManifestFactory, Sequence, Canvas, Image, Annotation, Manifest, Range
from scan_explorer_service.models import Article, Page, JournalVolume


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

    def create_manifest_from_volume(self, volume: JournalVolume):
        manifest = self.manifest(
            ident=f'{volume.id}/manifest.json', label="journal.volume")
        manifest.description = 'journal.description'
        manifest.add_sequence(self.create_sequence_from_volume(volume))
        for range in self.create_ranges_from_volume(volume):
            manifest.add_range(range)

        return manifest

    def create_sequence_from_volume(self, volume: JournalVolume) -> Sequence:
        sequence: Sequence = self.sequence()
        for page in volume.pages:
            sequence.add_canvas(self.get_or_create_canvas(page))
        
        return sequence

    def create_ranges_from_volume(self, volume: JournalVolume) -> Iterable[Sequence]:
        articles_done = []
        for page in volume.pages:
            for article in page.articles:
                if article not in articles_done:
                    articles_done.append(article)
                    yield self.create_range(article)

    def create_sequence(self, article: Article):
        sequence: Sequence = self.sequence()
        for page in article.pages:
            sequence.add_canvas(self.get_or_create_canvas(page))

        return sequence

    def create_range(self, article: Article):
        range: Range = self.range(ident=article.bibcode, label=article.bibcode)
        for page in article.pages:
            range.add_canvas(self.get_or_create_canvas(page))


        return range

    def get_canvas_dict(self) -> Dict[str, Canvas]:
        if not hasattr(self, 'canvas_dict'):
            self.canvas_dict = {}
        return self.canvas_dict

    def get_or_create_canvas(self, page: Page):
        canvas_dict = self.get_canvas_dict()
        if(page.id in canvas_dict.keys()):
            return canvas_dict[page.id]
        canvas: Canvas = self.canvas(ident=str(page.id), label=f'p. {page.label}')
        canvas.height = page.height
        canvas.width = page.width
        annotation = self.create_image_annotation(page)
        annotation.on = canvas.id
        canvas.add_annotation(annotation)
        canvas_dict[page.id] = canvas
        return canvas

    def create_image_annotation(self, page: Page):
        annotation: Annotation = self.annotation(ident=str(page.id))
        image: Image = annotation.image(
            ident=page.image_path, label=f'p. {page.label}', iiif=True)

        image.id = image.id.replace('/default.jpg', '/default.tif')

        image.format = page.format
        image.height = page.height
        image.width = page.width

        return annotation

    def add_search_service(self, manifest: Manifest, search_url: str):
        context = 'http://iiif.io/api/search/1/context.json'
        profile = 'http://iiif.io/api/search/1/search'
        
        manifest.add_service(ident=search_url, context=context, profile=profile)
