from django.template import Library
from django.template.defaultfilters import stringfilter
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

register = Library()


@register.filter(needs_autoescape=True)
@stringfilter
def add_class(html, css_class, autoescape=True):
    """Appends given css class to first passed html tag"""

    from html.parser import HTMLParser

    if autoescape:
        html = conditional_escape(html)
        css_class = conditional_escape(css_class)

    class CustomTagParser(HTMLParser):
        new_tag = ""
        class_added = False

        def add_class(self, tag, attrs):

            self.new_tag = self.new_tag + "<" + tag
            for key, value in attrs:
                if value:
                    if key == "class" and not self.class_added:
                        self.new_tag = (
                            self.new_tag
                            + " "
                            + key
                            + '="'
                            + value
                            + " "
                            + css_class
                            + '" '
                        )
                        self.class_added = True
                    else:
                        self.new_tag = (
                            self.new_tag + " " + key + '="' + value + '" '
                        )
                else:
                    self.new_tag = f"{self.new_tag} {key} "

            if not self.class_added:
                self.new_tag = self.new_tag + 'class="' + css_class + '" '
                self.class_added = True

            return

        def handle_starttag(self, tag, attrs):
            self.add_class(tag, attrs)

            self.new_tag = self.new_tag + ">"

            return

        def handle_startendtag(self, tag, attrs):
            self.add_class(tag, attrs)

            self.new_tag = self.new_tag + "/>"

            return

        def handle_data(self, data):
            self.new_tag = self.new_tag + data

            return

        def handle_endtag(self, tag):
            self.new_tag = self.new_tag + "</" + tag + ">"

            return

    parser = CustomTagParser()
    parser.feed(html)

    return mark_safe(parser.new_tag)
