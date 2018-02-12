#!/usr/bin/env python

import re
from calendar import month_name

import click
from pybtex.database.input import bibtex
import jinja2
import jinja2.sandbox


_months = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
}


def _author_fmt(author):
    return u' '.join(author.first() + author.middle() + author.last())

def _unlatex(string):
    """ Remove curly braces and other latex guff that we don't want for html output"""
    for x,y in [('{',''),('}',''),('\&','&')]:
        string = string.replace(x,y)
    return string

def _andlist(ss, sep=', ', seplast=', and ', septwo=' and '):
    if len(ss) <= 1:
        return ''.join(ss)
    elif len(ss) == 2:
        return septwo.join(ss)
    else:
        return sep.join(ss[:-1]) + seplast + ss[-1]


def _author_list(authors):
    return _andlist(list(map(_author_fmt, authors)))


def _venue_type(entry):
    venuetype = ''
    f = entry.fields
    if entry.type == 'inbook':
        venuetype = 'Chapter in '
    elif entry.type == 'techreport':
        venuetype = 'Technical Report '
    elif entry.type == 'phdthesis':
        venuetype = 'Ph.D. thesis, {}'.format(f['school'])
    elif entry.type == 'mastersthesis':
        venuetype = 'Master\'s thesis, {}'.format(f['school'])
    elif entry.type == 'unpublished':
        if 'howpublished' in f: 
            venuetype='Unpublished {}. '.format(_unlatex(f['howpublished']))
        elif 'type' in f:
            venuetype='Unpublished (type={}). '.format(f['type'])
        else:
            venuetype='Unpublished. '
    return venuetype


def _venue(entry):
    f = entry.fields
    venue = ''
    if entry.type == 'article':
        # biblatex uses journaltitle instead of journal
        if 'journal' in f:
            venue = f['journal']
        elif 'journaltitle' in f:
            venue = f['journaltitle']
        else:
            raise ValueError('No valid journal title found for article')
        try:
            if f['volume'] and f['number']:
                venue += ' {0}({1})'.format(f['volume'], f['number'])
        except KeyError:
            pass
    elif entry.type == 'inproceedings':
        venue = _unlatex(f['booktitle'])
        try:
            if f['series']:
                venue += ' ({})'.format(f['series'])
        except KeyError:
            pass
    elif entry.type == 'inbook':
        venue = f['title']
    elif entry.type == 'techreport':
        venue = '{0}, {1}'.format(f['number'], f['institution'])
    elif entry.type == 'phdthesis' or entry.type == 'mastersthesis':
        venue = ''
    elif entry.type == 'unpublished':
        if 'eventtitle' in f:
           venue = _unlatex(f['eventtitle'])
        else:
            venue = ''
    return venue


def _title(entry):
    if entry.type == 'inbook':
        title = entry.fields['chapter']
    else:
        title = entry.fields['title']
    return _unlatex(title)


def _main_url(entry):
    urlfields = ('url', 'ee')
    for f in urlfields:
        if f in entry.fields:
            return entry.fields[f]
    return None


def _doi(entry):
    if 'doi' in entry.fields:
        return entry.fields['doi']
    else:
        return ''


def _extra_urls(entry):
    """Returns a dict of URL types to URLs, e.g.
       { 'nytimes': 'http://nytimes.com/story/about/research.html',
          ... }
    """
    urls = {}
    for k, v in entry.fields.items():
        k = k.lower()
        if not k.endswith('_url'):
            continue
        k = k[:-4]
        urltype = k.replace('_', ' ')
        urls[urltype] = v
    return urls


def _month_match(mon):
    if re.match('^[0-9]+$', mon):
        return int(mon)
    return _months[mon.lower()[:3]]


def _month_name(monthnum):
    try:
        return month_name[int(monthnum)]
    except (ValueError, KeyError):
        return ''


def _sortkey(entry):
    e = entry.fields
    year = '{:04d}'.format(int(e['year']))
    try:
        monthnum = _month_match(e['month'])
        year += '{:02d}'.format(monthnum)
    except KeyError:
        year += '00'
    return year


@click.command()
@click.argument('bibfile', metavar='BIBFILE.bib', type=click.File('r'))
@click.argument('template', metavar='TEMPLATE.html', type=click.File('r'))
@click.option('-o', '--output', type=click.File('w'))
def main(bibfile, template, output):
    # pylint: disable=unused-argument
    """Render a bibtex .bib file to HTML using an HTML template."""
    tenv = jinja2.sandbox.SandboxedEnvironment()
    tenv.filters['author_fmt'] = _author_fmt
    tenv.filters['author_list'] = _author_list
    tenv.filters['title'] = _title
    tenv.filters['venue_type'] = _venue_type
    tenv.filters['venue'] = _venue
    tenv.filters['main_url'] = _main_url
    tenv.filters['extra_urls'] = _extra_urls
    tenv.filters['monthname'] = _month_name
    tenv.filters['doi'] = _doi
    tmpl = tenv.from_string(template.read())

    # Parse the BibTeX file.
    db = bibtex.Parser().parse_stream(bibfile)

    # Include the bibliography key in each entry.
    for k, v in db.entries.items():
        v.fields['key'] = k
        # handle biblatex dates 
        if 'year' not in v.fields:
            if 'date' not in v.fields:
                raise ValueError('No valid date for %s' % k)
            else:
                v.fields['year'] = v.fields['date'][0:4]
                if len(v.fields['date'])>=7:
                    v.fields['month']=v.fields['date'][5:7]

    # Render the template.
    bib_sorted = sorted(db.entries.values(), key=_sortkey, reverse=True)
    out = tmpl.render(entries=bib_sorted)
    print (out)


if __name__ == '__main__':
    # pylint: disable=no-value-for-parameter
    main()
