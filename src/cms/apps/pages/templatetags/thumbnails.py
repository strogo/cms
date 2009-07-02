"""Template tags used to generate thumbnails."""


import re

from django import template
from django.core.exceptions import ObjectDoesNotExist
from django.forms.util import flatatt

from cms.apps.pages import permalinks
from cms.apps.pages import permalinks, thumbnails


register = template.Library()


RE_THUMBNAIL = re.compile(r"^(\w+)\W+([\w\.]+)\W+(\d+)\W+(\d+)$")

RE_THUMBNAIL_ALIAS = re.compile(RE_THUMBNAIL.pattern[:-1] + r"\W+as\W+(\w+)$") 


class ThumbnailNode(template.Node):
    
    """Renders the thumbnail tag."""
    
    def __init__(self, token, method):
        """Initializes the ThumbnailNode."""
        # Parse the token.
        match = RE_THUMBNAIL_ALIAS.match(token.contents)
        if match:
            tag_name, image, width, height, alias = match.groups()
        else:
            match = RE_THUMBNAIL.match(token.contents)
            if match:
                tag_name, image, width, height = match.groups()
                alias = None
            else:
                bits = token.split_contents()
                raise template.TemplateSyntaxError, "Invalid syntax for %s tag." % bits[0]
        # Store the result of the parse.
        self.image = template.Variable(image)
        self.width = int(width)
        self.height = int(height)
        self.alias = alias
        self.method = method
        
    def render(self, context):
        """Renders the thumbnail."""
        image = self.image.resolve(context)
        thumbnail = thumbnails.generate(image, self.width, self.height, self.method)
        # Set an alias, if specified.
        if self.alias:
            context[self.alias] = thumbnail
            return ""
        # Generate the image tag.
        return '<img src="%s" width="%s" height="%s" alt=""/>' % (thumbnail.url, thumbnail.width, thumbnail.height)


@register.tag
def thumbnail(parser, token):
    """
    Generates a thumbnail of the given image, preserving aspect ratio.
    
    This has the syntax:
    
        {% thumbnail image width height %}
        
    The output will be a HTML image tag.
    
    Alternatively, you can specify an alias for the image as follows:
    
        {% thumbnail image width height as alias %}
        
    This will put an thumbnail variable into the context under the given name.
    The thumbnail variable will be of type ImageFile, allowing its url, width
    and height to be accessed.
    """
    return ThumbnailNode(token, thumbnails.THUMBNAIL)
    
    
@register.tag
def resize(parser, token):
    """
    Generates a resized thumbnail of the given image, ignoring aspect ratio.
    
    See the 'thumbnail' tag for appropriate syntax.
    """
    return ThumbnailNode(token, thumbnails.RESIZE)


@register.tag
def crop(parser, token):
    """
    Generates a cropped thumbnail of the given image, preserving aspect ratio.
    
    See the 'thumbnail' tag for appropriate syntax.
    """
    return ThumbnailNode(token, thumbnails.CROP)


RE_IMG = re.compile(r"<img(.+?)/>", re.IGNORECASE)

RE_ATTR = re.compile(r"""\s(\w+)=["']([^"']+)["']""", re.IGNORECASE)


@register.filter
def generate_thumbnails(text):
    """
    Generates thumbnails for all the permalinked images in the given HTML text.
    """
    offset = 0
    for match in RE_IMG.finditer(text):
        attrs = match.group(1)
        attr_dict = dict(RE_ATTR.findall(attrs))
        try:
            src = attr_dict["src"]
            width = int(attr_dict["width"])
            height = int(attr_dict["height"])
        except KeyError:
            continue
        except ValueError:
            continue
        try:
            obj = permalinks.resolve(src)
        except ObjectDoesNotExist:
            continue
        thumbnail = thumbnails.resize(obj.file, width, height)
        attr_dict["src"] = thumbnail.url
        attr_dict["width"] = thumbnail.width
        attr_dict["height"] = thumbnail.height
        new_attrs = flatatt(attr_dict)
        start = match.start(1)
        end = match.end(1)
        text = u"".join((text[:start+offset], new_attrs, text[end+offset:]))
        offset += len(new_attrs) - len(attrs)
    return text 
        
    