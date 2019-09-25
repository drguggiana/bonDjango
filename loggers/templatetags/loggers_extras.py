import re
from django import template
from django.utils.safestring import SafeData, mark_safe
from django.utils.html import escape, smart_urlquote
from django.utils.encoding import force_text

register = template.Library()

# This entire filter is almost identical to urlize_quoted_links from the DRF template tags, but I modified it to add
# the last part of the url (PK) to the link instead of the whole thing to make the links look more intuitive

# Bunch of stuff cloned from urlize
TRAILING_PUNCTUATION = ['.', ',', ':', ';', '.)', '"', "']", "'}", "'"]
WRAPPING_PUNCTUATION = [('(', ')'), ('<', '>'), ('[', ']'), ('&lt;', '&gt;'),
                        ('"', '"'), ("'", "'")]
word_split_re = re.compile(r'(\s+)')
simple_url_re = re.compile(r'^https?://\[?\w', re.IGNORECASE)
simple_url_2_re = re.compile(r'^www\.|^(?!http)\w[^@]+\.(com|edu|gov|int|mil|net|org)$', re.IGNORECASE)
simple_email_re = re.compile(r'^\S+@\S+\.\S+$')


def smart_urlquote_wrapper(matched_url):
    """
    Simple wrapper for smart_urlquote. ValueError("Invalid IPv6 URL") can
    be raised here, see issue #1386
    """
    try:
        return smart_urlquote(matched_url)
    except ValueError:
        return None


@register.filter(name='urlize_mod')
def urlize_mod(text, trim_url_limit=None, nofollow=True, autoescape=True):
    def trim_url(x, limit=trim_url_limit):
        return limit is not None and (len(x) > limit and ('%s...' % x[:max(0, limit - 3)])) or x

    safe_input = isinstance(text, SafeData)

    # Unfortunately, Django built-in cannot be used here, because escaping
    # is to be performed on words, which have been forcibly coerced to text
    def conditional_escape(text):
        return escape(text) if autoescape and not safe_input else text

    words = word_split_re.split(force_text(text))
    for i, word in enumerate(words):
        if '.' in word or '@' in word or ':' in word:
            # Deal with punctuation.
            lead, middle, trail = '', word, ''
            for punctuation in TRAILING_PUNCTUATION:
                if middle.endswith(punctuation):
                    middle = middle[:-len(punctuation)]
                    trail = punctuation + trail
            for opening, closing in WRAPPING_PUNCTUATION:
                if middle.startswith(opening):
                    middle = middle[len(opening):]
                    lead = lead + opening
                # Keep parentheses at the end only if they're balanced.
                if (
                    middle.endswith(closing) and
                    middle.count(closing) == middle.count(opening) + 1
                ):
                    middle = middle[:-len(closing)]
                    trail = closing + trail

            # Make URL we want to point to.
            url = None
            nofollow_attr = ' rel="nofollow"' if nofollow else ''
            if simple_url_re.match(middle):
                url = smart_urlquote_wrapper(middle)
            elif simple_url_2_re.match(middle):
                url = smart_urlquote_wrapper('http://%s' % middle)
            elif ':' not in middle and simple_email_re.match(middle):
                local, domain = middle.rsplit('@', 1)
                try:
                    domain = domain.encode('idna').decode('ascii')
                except UnicodeError:
                    continue
                url = 'mailto:%s@%s' % (local, domain)
                nofollow_attr = ''

            # Make link.
            if url:
                trimmed = trim_url(middle)
                lead, trail = conditional_escape(lead), conditional_escape(trail)
                url, trimmed = conditional_escape(url), conditional_escape(trimmed)
                # get only the last part of the url (pk)
                url_pk = trimmed.split('/')
                # load that as the link text
                middle = '<a href="%s"%s>%s</a>' % (url, nofollow_attr, url_pk[-2])

                words[i] = '%s%s%s' % (lead, middle, trail)
            else:
                words[i] = conditional_escape(word)
        else:
            words[i] = conditional_escape(word)
    return mark_safe(''.join(words))


