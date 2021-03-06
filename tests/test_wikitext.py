﻿"""Test the functions of wikitext.py module."""
from operator import attrgetter
from unittest import expectedFailure, main, TestCase

from wikitextparser import WikiText, parse, Template, ParserFunction
# noinspection PyProtectedMember
from wikitextparser._wikitext import WS


class TestWikiText(TestCase):

    """Test the basics  of the WikiText class."""

    def test_len(self):
        ae = self.assertEqual
        t1, t2 = WikiText('{{t1|{{t2}}}}').templates
        ae(len(t2), 6)
        ae(len(t1), 13)

    def test_repr(self):
        self.assertEqual(repr(parse('')), "WikiText('')")

    def test_call(self):
        ae = self.assertEqual
        t1, t2 = WikiText('{{t1|{{t2}}}}').templates
        ae(t2(2), 't')
        ae(t2(2, 4), 't2')
        ae(t2(-4, -2), 't2')
        ae(t2(-3), '2')

    def test_getitem(self):
        ae = self.assertEqual
        wt = WikiText('a')
        with self.assertRaises(NotImplementedError):
            ae(wt[0], 'a')

    def test_setitem(self):
        ae = self.assertEqual
        s = '{{t1|{{t2}}}}'
        wt = WikiText(s)
        t1, t2 = wt.templates
        t2[2] = 'a'
        ae(t2.string, '{{a2}}')
        ae(t1.string, '{{t1|{{a2}}}}')
        t2[2] = 'bb'
        ae(t2.string, '{{bb2}}')
        ae(t1.string, '{{t1|{{bb2}}}}')
        t2[2:5] = 'ccc'
        ae(t2.string, '{{ccc}}')
        ae(t1.string, '{{t1|{{ccc}}}}')
        t2[-5:-2] = 'd'
        ae(wt.string, '{{t1|{{d}}}}')
        t2[-3] = 'e'
        ae(wt.string, '{{t1|{{e}}}}')

    def test_setitem_errors(self):
        ae = self.assertEqual
        w = WikiText('a')
        self.assertRaises(IndexError, w.__setitem__, -2, 'b')
        ae('a', w(-9, 9))
        self.assertRaises(IndexError, w.__setitem__, 1, 'c')
        self.assertRaises(
            NotImplementedError, w.__setitem__, slice(0, 1, 1), 'd')
        ae('a', w(-1, None))
        ae(w(-2, None), 'a')
        self.assertRaises(IndexError, w.__setitem__, slice(-2, None), 'e')
        ae(w(0, -2), '')
        self.assertRaises(IndexError, w.__setitem__, slice(0, -2), 'f')
        w[0] = 'gg'
        w[1] = 'hh'
        ae(w.string, 'ghh')
        # stop and start in range but stop is before start
        ae(w(1, 0), '')
        self.assertRaises(IndexError, w.__setitem__, slice(1, 0), 'h')

    def test_insert(self):
        ae = self.assertEqual
        w = WikiText('c')
        w.insert(0, 'a')
        ae(w.string, 'ac')
        # Just to show that ``w.insert(i, s)`` is the same as ``w[i:i] = s``:
        v = WikiText('c')
        v[0:0] = 'a'
        ae(w.string, v.string)
        w.insert(-1, 'b')
        ae(w.string, 'abc')
        # Like list.insert, w.insert accepts out of range indexes.
        w.insert(5, 'd')
        ae(w.string, 'abcd')
        w.insert(-5, 'z')
        ae(w.string, 'zabcd')

    def test_overwriting_template_args(self):
        ae = self.assertEqual
        t = Template('{{t|a|b|c}}')
        c = t.arguments[-1]
        ae('|c', c.string)
        t.string = '{{t|0|a|b|c}}'
        ae('', c.string)
        ae('0', t.get_arg('1').value)
        ae('c', t.get_arg('4').value)

    def test_delitem(self):
        ae = self.assertEqual
        s = '{{t1|{{t2}}}}'
        wt = WikiText(s)
        t1, t2 = wt.templates
        del t2[3]
        ae(wt.string, '{{t1|{{t}}}}')
        del wt[5:10]
        ae(t1.string, '{{t1|}}')
        ae(t2.string, '')

    def test_span(self):
        self.assertEqual(WikiText('').span, (0, 0))


class Contains(TestCase):

    """Test the __contains__ method of the WikiText class."""

    def test_a_is_actually_in_b(self):
        b, a = WikiText('{{b|{{a}}}}').templates
        self.assertIn(a, b)
        self.assertNotIn(b, a)

    def test_a_seems_to_be_in_b_but_in_another_span(self):
        ani = self.assertNotIn
        s = '{{b|{{a}}}}{{a}}'
        b, a1, a2 = WikiText(s).templates
        self.assertIn(a1, b)
        ani(a2, b)
        ani(a2, a1)
        ani(a1, a2)

    def test_a_b_from_different_objects(self):
        ai = self.assertIn
        ani = self.assertNotIn
        s = '{{b|{{a}}}}'
        b1, a1 = WikiText(s).templates
        b2, a2 = WikiText(s).templates
        ai(a1, b1)
        ai(a2, b2)
        ani(a2, b1)
        ani(a1, b2)
        ai('{{a}}', b1)
        ani('{{c}}', b2)


class ShrinkSpanUpdate(TestCase):

    """Test the _shrink_update method."""

    def test_stripping_template_name_should_update_its_arg_spans(self):
        t = Template('{{ t\n |1=2}}')
        a = t.arguments[0]
        t.name = t.name.strip(WS)
        self.assertEqual('|1=2', a.string)

    def test_opcodes_in_spans_should_be_referenced_based_on_self_lststr0(self):
        template = WikiText('{{a}}{{ b\n|d=}}').templates[1]
        arg = template.arguments[0]
        template.name = template.name.strip(WS)
        self.assertEqual('|d=', arg.string)

    def test_rmstart_s_rmstop_e(self):
        wt = WikiText('{{t| {{t2|<!--c-->}} }}')
        c = wt.comments[0]
        t = wt.templates[0]
        t[3:14] = ''
        self.assertEqual(c.string, 'c-->')

    def test_shrink_more_than_one_subspan(self):
        ae = self.assertEqual
        wt = WikiText('{{p|[[c1]][[c2]][[c3]]}}')
        wls = wt.wikilinks
        t = wt.templates[0]
        del t[:]
        ae(wls[0].string, '')
        ae(wls[1].string, '')
        ae(wls[2].string, '')


class CloseSubSpans(TestCase):

    """Test the _close_subspans method."""

    def test_spans_are_closed_properly(self):
        # Real example:
        # ae(
        #     '{{text\n    | 1 = {{#if:\n        \n        | \n    }}\n}}',
        #     WikiText('{{text|1={{#if:|}}\n\n}}').pformat(),
        # )
        wt = WikiText('')
        wt._type_to_spans = {'ParserFunction': [[16, 25]]}
        wt._close_subspans(16, 27)
        self.assertFalse(wt._type_to_spans['ParserFunction'])

    def test_rm_start_not_equal_to_self_start(self):
        wt = WikiText('t{{a}}')
        wt._type_to_spans = {'Templates': [[1, 6]]}
        wt._close_subspans(5, 6)
        self.assertEqual(wt._type_to_spans, {'Templates': [[1, 6]]})


class ExpandSpanUpdate(TestCase):

    """Test the _expand_span_update method."""

    def test_extending_template_name_should_not_effect_arg_string(self):
        t = Template('{{t|1=2}}')
        a = t.arguments[0]
        t.name = 't\n    '
        self.assertEqual('|1=2', a.string)

    def test_overwriting_or_extending_selfspan_will_cause_data_loss(self):
        ae = self.assertEqual
        wt = WikiText('{{t|{{#if:a|b|c}}}}')
        a = wt.templates[0].arguments[0]
        pf = wt.parser_functions[0]
        a.value += ''
        ae('|{{#if:a|b|c}}', a.string)
        # Note that the old parser function is overwritten
        ae('', pf.string)
        pf = a.parser_functions[0]
        a.value = 'a'
        ae('', pf.string)


class Templates(TestCase):

    """Test WikiText.templates."""

    def test_template_inside_wikilink(self):
        self.assertEqual(2, len(WikiText(
            "{{text |  [[ A | {{text|b}} ]] }}").templates))

    def test_wikilink_in_template(self):
        # todo: merge with test_spans?
        ae = self.assertEqual
        s = "{{text |[[A|}}]]}}"
        ts = str(WikiText(s).templates[0])
        ae(s, ts)
        ae(s, str(WikiText('<ref>{{text |[[A|}}]]}}</ref>').templates[0]))

    def test_wikilink_containing_closing_braces_in_template(self):
        s = '{{text|[[  A   |\n|}}[]<>]]\n}}'
        self.assertEqual(s, str(WikiText(s).templates[0]))

    def test_ignore_comments(self):
        s1 = "{{text |<!-- }} -->}}"
        self.assertEqual(s1, str(WikiText(s1).templates[0]))

    def test_ignore_nowiki(self):
        self.assertEqual("{{text |<nowiki>}} A </nowiki> }}", str(WikiText(
            "{{text |<nowiki>}} A </nowiki> }} B").templates[0]))

    def test_template_inside_extension_tags(self):
        s = "<includeonly>{{t}}</includeonly>"
        self.assertEqual('{{t}}', str(WikiText(s).templates[0]))

    def test_dont_parse_source_tag(self):
        s = "<source>{{t}}</source>"
        self.assertEqual(0, len(WikiText(s).templates))


class ParserFunctions(TestCase):

    """Test WikiText.parser_functions."""

    def test_comment_in_parserfunction_name(self):
        s = "{{<!--c\n}}-->#if:|a}}"
        self.assertEqual(1, len(WikiText(s).parser_functions))


class WikiLinks(TestCase):

    """Test WikiText.wikilinks."""

    def test_wikilink_inside_parser_function(self):
        self.assertEqual("[[u:{{{3}}}|{{{3}}}]]", WikiText(
            "{{ #if: {{{3|}}} | [[u:{{{3}}}|{{{3}}}]] }}").wikilinks[0].string)

    def test_template_in_wikilink(self):
        s = '[[A|{{text|text}}]]'
        self.assertEqual(s, str(WikiText(s).wikilinks[0]))

    def test_wikilink_target_may_contain_newline(self):
        s = '[[A | faf a\n\nfads]]'
        self.assertEqual(s, str(WikiText(s).wikilinks[0]))


class Comments(TestCase):

    """Test the WikiText.commonts."""

    def test_getting_comment(self):
        self.assertEqual("\n\ncomment\n{{A}}\n", WikiText(
            'text1 <!--\n\ncomment\n{{A}}\n-->text2').comments[0].contents)


class ExternalLinks(TestCase):

    """Test the WikiText.external_links."""

    def test_ipv6_brackets(self):
        ae = self.assertEqual
        # See:
        # https://en.wikipedia.org/wiki/IPv6_address#Literal_IPv6_addresses_in_network_resource_identifiers
        ae(
            parse('https://[2001:db8:85a3:8d3:1319:8a2e:370:7348]:443/')
            .external_links[0].url,
            'https://[2001:db8:85a3:8d3:1319:8a2e:370:7348]:443/')
        el = parse(
            '[https://[2001:db8:85a3:8d3:1319:8a2e:370:7348]:443/ t]'
        ).external_links[0]
        ae(el.url, 'https://[2001:db8:85a3:8d3:1319:8a2e:370:7348]:443/')
        ae(el.text, 't')
        s = '[//[fe80::1ff:fe23:4567:890a]:443/ t]'
        ae(parse(s).external_links[0].string, s)

    def test_in_template(self):
        ae = self.assertEqual
        # with brackets
        els = parse('{{text|http://example.com?foo=bar}}').external_links
        ae(len(els), 1)
        ae(els[0].url, 'http://example.com?foo=bar')
        # without brackets
        els = parse('{{text|[http://example.com?foo=bar]}}').external_links
        ae(len(els), 1)
        ae(els[0].url, 'http://example.com?foo=bar')

    def test_starting_boundary(self):
        self.assertFalse(parse('turn:a').external_links)

    def test_external_links_inside_template(self):
        t = Template('{{t0|urn:0{{t1|urn:1}}}}')
        # Warning: both urn's are treated ast one.
        # But on a live site this depends on the template outcome.
        self.assertEqual(t.external_links[0].string, 'urn:0')

    def test_bare_link(self):
        s = 'text1 HTTP://mediawiki.org text2'
        wt = WikiText(s)
        self.assertEqual(
            'HTTP://mediawiki.org',
            str(wt.external_links[0]))

    def test_with_lable(self):
        ae = self.assertEqual
        s = 'text1 [http://mediawiki.org MediaWiki] text2'
        el = WikiText(s).external_links[0]
        ae('http://mediawiki.org', el.url)
        ae('MediaWiki', el.text)

    def test_external_link_match_is_not_in_spans(self):
        ae = self.assertEqual
        wt = WikiText('t [http://b.b b] t [http://c.c c] t')
        # calculate the links
        links1 = wt.external_links
        wt.insert(0, 't [http://a.a a]')
        links2 = wt.external_links
        ae(links1[1].string, '[http://c.c c]')
        ae(links2[0].string, '[http://a.a a]')

    def test_numbered_link(self):
        s = 'text1 [http://mediawiki.org] text2'
        wt = WikiText(s)
        self.assertEqual('[http://mediawiki.org]', str(wt.external_links[0]))

    def test_protocol_relative(self):
        s = 'text1 [//en.wikipedia.org wikipedia] text2'
        wt = WikiText(s)
        self.assertEqual(
            '[//en.wikipedia.org wikipedia]', str(wt.external_links[0]))

    def test_destroy(self):
        s = 'text1 [//en.wikipedia.org wikipedia] text2'
        wt = WikiText(s)
        del wt.external_links[0].string
        self.assertEqual('text1  text2', str(wt))

    def test_wikilink2externallink_fallback(self):
        ae = self.assertEqual
        p = parse('[[http://example.com foo bar]]')
        ae('[http://example.com foo bar]', p.external_links[0].string)
        ae(0, len(p.wikilinks))

    def test_template_in_link(self):
        ae = self.assertEqual
        # Note: In reality all assertions depend on the template outcome.
        ae(  # expected
            parse('http://example.com{{dead link}}').external_links[0].url,
            'http://example.com')
        ae(  # unexpected
            parse('http://example.com/foo{{!}}bar').external_links[0].url,
            'http://example.com/foo')
        ae(  # depends on {{foo}} contents
            parse('[http://example.com{{foo}}text]').external_links[0].url,
            'http://example.com')
        ae(  # depends on {{foo bar}} contents
            parse('[http://example.com{{foo bar}} t]').external_links[0].url,
            'http://example.com')

    def test_comment_in_external_link(self):
        ae = self.assertEqual
        # This probably can be fixed, but who uses comments within urls?
        el = parse(
            '[http://example.com/foo<!-- comment -->bar]').external_links[0]
        self.assertIsNone(el.text)
        ae(el.url, 'http://example.com/foo<!-- comment -->bar')
        ae(
            parse('[http://example<!-- c -->.com t]').external_links[0].url,
            'http://example<!-- c -->.com')

    def test_no_bare_external_link_within_wiki_links(self):
        ae = self.assertEqual
        """A wikilink's target may not be an external link."""
        p = parse('[[ https://w|b]]')
        ae('https://w|b', p.external_links[0].string)
        ae(0, len(p.wikilinks))

    def test_bare_external_link_must_have_scheme(self):
        """Bare external links must have scheme."""
        self.assertEqual(len(parse('//mediawiki.org').external_links), 0)

    def test_external_link_with_template(self):
        """External links may contain templates."""
        self.assertEqual(
            len(parse('http://example.com/{{text|foo}}').external_links), 1)

    def test_external_link_containing_extension_tags(self):
        ae = self.assertEqual
        s = '[https://www.google.<includeonly>com </includeonly>a]'
        el = parse(s).external_links[0]
        ae(str(el), s)
        # Warning: This depends on context and/or requires evaluation.
        self.assertNotEqual(
            el.url, 'https://www.google.a')
        s = '[https://www.google.<noinclude>com </noinclude>a]'
        el = parse(s).external_links[0]
        ae(str(el), s)
        # Warning: This depends on context and/or requires evaluation.
        self.assertNotEqual(el.url, 'https://www.google.com')

    def test_parser_function_in_external_link(self):
        ae = self.assertEqual
        ae(parse(
            '[urn:u {{<!--c-->#if:a|a}}]'
        ).external_links[0].parser_functions[0].string, '{{<!--c-->#if:a|a}}')
        # Note: Depends on the parser function outcome.
        ae(len(parse('[urn:{{#if:a|a|}} t]').external_links), 0)

    def test_equal_span_ids(self):
        p = parse('lead\n== 1 ==\nhttp://wikipedia.org/')
        self.assertEqual(
            id(p.external_links[0]._span),
            id(p.sections[1].external_links[0]._span))


class Tables(TestCase):

    """Test the tables property."""

    def test_table_extraction(self):
        s = '{|class=wikitable\n|a \n|}'
        p = parse(s)
        self.assertEqual(s, p.tables[0].string)

    def test_table_start_after_space(self):
        s = '   {|class=wikitable\n|a \n|}'
        p = parse(s)
        self.assertEqual(s.strip(WS), p.tables[0].string)

    def test_ignore_comments_before_extracting_tables(self):
        s = '{|class=wikitable\n|a \n<!-- \n|} \n-->\n|b\n|}'
        p = parse(s)
        self.assertEqual(s, p.tables[0].string)

    def test_two_tables(self):
        ae = self.assertEqual
        s = 'text1\n {|\n|a \n|}\ntext2\n{|\n|b\n|}\ntext3\n'
        p = parse(s)
        tables = p.tables
        ae(2, len(tables))
        ae('{|\n|a \n|}', tables[0].string)
        ae('{|\n|b\n|}', tables[1].string)

    def test_nested_tables(self):
        ae = self.assertEqual
        s = 'text1\n{|class=wikitable\n|a\n|\n' \
            '{|class=wikitable\n|b\n|}\n|}\ntext2'
        p = parse(s)
        ae(1, len(p.get_tables()))  # non-recursive
        tables = p.tables  # recursive
        ae(2, len(tables))
        table0 = tables[0]
        ae(s[6:-6], table0.string)
        ae(0, table0.nesting_level)
        table1 = tables[1]
        ae('{|class=wikitable\n|b\n|}', table1.string)
        ae(1, table1.nesting_level)

    def test_tables_in_different_sections(self):
        s = '{|\n| a\n|}\n\n= s =\n{|\n| b\n|}\n'
        p = parse(s).sections[1]
        self.assertEqual('{|\n| b\n|}', p.tables[0].string)

    def test_match_index_is_none(self):
        ae = self.assertEqual
        wt = parse('{|\n| b\n|}\n')
        assert len(wt.tables) == 1
        wt.insert(0, '{|\n| a\n|}\n')
        tables = wt.tables
        ae(tables[0].string, '{|\n| a\n|}')
        ae(tables[1].string, '{|\n| b\n|}')

    def test_tables_may_be_indented(self):
        s = ' ::{|class=wikitable\n|a\n|}'
        wt = parse(s)
        self.assertEqual(wt.tables[0].string, '{|class=wikitable\n|a\n|}')

    def test_comments_before_table_start(self):
        s = ' <!-- c -->::{|class=wikitable\n|a\n|}'
        wt = parse(s)
        self.assertEqual(wt.tables[0].string, '{|class=wikitable\n|a\n|}')

    def test_comments_between_indentation(self):
        s = ':<!-- c -->:{|class=wikitable\n|a\n|}'
        wt = parse(s)
        self.assertEqual(wt.tables[0].string, '{|class=wikitable\n|a\n|}')

    def test_comments_between_indentation_after_them(self):
        s = ':<!-- c -->: <!-- c -->{|class=wikitable\n|a\n|}'
        wt = parse(s)
        self.assertEqual(wt.tables[0].string, '{|class=wikitable\n|a\n|}')

    def test_indentation_cannot_be_inside_nowiki(self):
        """A very unusual case. It would be OK to have false positives here.

        Also false positive for tables are pretty much harmless here.

        The same thing may happen for tables which start right after a
        templates, parser functions, wiki links, comments, or
        other extension tags.

        """
        self.assertEqual(len(parse(
            '<nowiki>:</nowiki>{|class=wikitable\n|a\n|}').tables), 0)

    def test_template_before_or_after_table(self):
        # This tests self._shadow function.
        s = '{{t|1}}\n{|class=wikitable\n|a\n|}\n{{t|1}}'
        p = parse(s)
        self.assertEqual([['a']], p.tables[0].data())

    def test_nested_tables_sorted(self):
        ae = self.assertEqual
        ai = self.assertIs
        s = (
            '{| style="border: 1px solid black;"\n'
            '| style="border: 1px solid black;" | 0\n'
            '| style="border: 1px solid black; text-align:center;" | 1\n'
            '{| style="border: 2px solid black; background: green;" '
            '<!-- The nested table must be on a new line -->\n'
            '| style="border: 2px solid darkgray;" | 1_G00\n'
            '|-\n'
            '| style="border: 2px solid darkgray;" | 1_G10\n'
            '|}\n'
            '| style="border: 1px solid black; vertical-align: bottom;" '
            '| 2\n'
            '| style="border: 1px solid black; width:100px" |\n'
            '{| style="border: 2px solid black; background: yellow"\n'
            '| style="border: 2px solid darkgray;" | 3_Y00\n'
            '|}\n'
            '{| style="border: 2px solid black; background: Orchid"\n'
            '| style="border: 2px solid darkgray;" | 3_O00\n'
            '| style="border: 2px solid darkgray;" | 3_O01\n'
            '|}\n'
            '| style="border: 1px solid black; width: 50px" |\n'
            '{| style="border: 2px solid black; background:blue; float:left"\n'
            '| style="border: 2px solid darkgray;" | 4_B00\n'
            '|}\n'
            '{| style="border: 2px solid black; background:red; float:right"\n'
            '| style="border: 2px solid darkgray;" | 4_R00\n'
            '|}\n'
            '|}')
        p = parse(s)
        ae(1, len(p.get_tables()))  # non-recursive
        tables = p.tables
        ae(tables, sorted(tables, key=attrgetter('_span')))
        t0 = tables[0]
        ae(s, t0.string)
        ae(t0.data(strip=False), [[
            ' 0',
            ' 1\n'
            '{| style="border: 2px solid black; background: green;" '
            '<!-- The nested table must be on a new line -->\n'
            '| style="border: 2px solid darkgray;" | 1_G00\n|-\n'
            '| style="border: 2px solid darkgray;" | 1_G10\n'
            '|}',
            ' 2',
            '\n{| style="border: 2px solid black; background: yellow"\n'
            '| style="border: 2px solid darkgray;" | 3_Y00\n|}\n'
            '{| style="border: 2px solid black; background: Orchid"\n'
            '| style="border: 2px solid darkgray;" | 3_O00\n'
            '| style="border: 2px solid darkgray;" | 3_O01\n|}',
            '\n{| style="border: 2px solid black; background:blue; float:left"'
            '\n| style="border: 2px solid darkgray;" | 4_B00\n|}\n'
            '{| style="border: 2px solid black; background:red; float:right"\n'
            '| style="border: 2px solid darkgray;" | 4_R00\n|}'
        ]])
        ae(tables[3].data(), [['3_O00', '3_O01']])
        ae(5, len(tables[0].tables))
        dynamic_spans = p._type_to_spans['Table']
        ae(len(dynamic_spans), 6)
        pre_insert_spans = dynamic_spans[:]
        p.insert(0, '{|\na\n|}\n')
        ae(len(dynamic_spans), 6)
        ae(2, len(p.get_tables()))  # non-recursive for the second time
        ae(len(dynamic_spans), 7)
        for os, ns in zip(dynamic_spans[1:], pre_insert_spans):
            ai(os, ns)


class IndentLevel(TestCase):

    """Test the nesting_level method of the WikiText class."""

    def test_a_in_b(self):
        ae = self.assertEqual
        s = '{{b|{{a}}}}'
        b, a = WikiText(s).templates
        ae(1, b.nesting_level)
        ae(2, a.nesting_level)


class TestPformat(TestCase):

    """Test the pformat method of the WikiText class."""

    def test_template_with_multi_args(self):
        wt = WikiText('{{a|b=b|c=c|d=d|e=e}}')
        self.assertEqual(
            '{{a\n    | b = b\n    | c = c\n    | d = d\n    | e = e\n}}',
            wt.pformat())

    def test_double_space_indent(self):
        s = "{{a|b=b|c=c|d=d|e=e}}"
        wt = WikiText(s)
        self.assertEqual(
            '{{a\n  | b = b\n  | c = c\n  | d = d\n  | e = e\n}}',
            wt.pformat('  '))

    def test_remove_comments(self):
        self.assertEqual(
            '{{a\n  | e = e\n}}',
            WikiText('{{a|<!--b=b|c=c|d=d|-->e=e}}').pformat('  ', True))

    def test_first_arg_of_tag_is_whitespace_sensitive(self):
        """The second argument of #tag is an exception.

        See the last warning on [[mw:Help:Magic_words#Miscellaneous]]:
        You must write {{#tag:tagname||attribute1=value1|attribute2=value2}}
        to pass an empty content. No space is permitted in the area reserved
        for content between the pipe characters || before attribute1.
        """
        ae = self.assertEqual
        s = '{{#tag:ref||name="n1"}}'
        wt = WikiText(s)
        ae(s, wt.pformat())
        s = '{{#tag:foo| }}'
        wt = WikiText(s)
        ae(s, wt.pformat())

    def test_invoke(self):
        """#invoke args are also whitespace-sensitive."""
        s = '{{#invoke:module|func|arg}}'
        wt = WikiText(s)
        self.assertEqual(s, wt.pformat())

    def test_on_parserfunction(self):
        s = "{{#if:c|abcde = f| g=h}}"
        wt = parse(s)
        self.assertEqual(
            '{{#if:\n'
            '    c\n'
            '    | abcde = f\n'
            '    | g=h\n'
            '}}',
            wt.pformat())

    def test_parserfunction_with_no_pos_arg(self):
        s = "{{#switch:case|a|b}}"
        wt = parse(s)
        self.assertEqual(
            '{{#switch:\n'
            '    case\n'
            '    | a\n'
            '    | b\n'
            '}}',
            wt.pformat())

    def test_convert_positional_to_keyword_if_possible(self):
        self.assertEqual(
            '{{t\n    | 1 = a\n    | 2 = b\n    | 3 = c\n}}',
            parse('{{t|a|b|c}}').pformat())

    def test_inconvertible_positionals(self):
        """Otherwise the second positional arg will also be passed as 1.

        Because of T24555 we can't use "<nowiki/>" to preserve the
        whitespace of positional arguments. On the other hand we can't just
        convert the initial arguments to keyword and keep the rest as
        positional, because that would produce duplicate args as stated above.

        What we *can* do is to either convert all the arguments to keyword
        args if possible, or we should only convert the longest part of
        the tail of arguments that is convertible.

        Use <!--comments--> to align positional arguments where necessary.

        """
        ae = self.assertEqual
        ae(
            '{{t\n'
            '    |a<!--\n'
            ' -->| b <!--\n'
            '-->}}',
            parse('{{t|a| b }}').pformat())
        ae(
            '{{t\n'
            '    | a <!--\n'
            ' -->| 2 = b\n'
            '    | 3 = c\n'
            '}}',
            parse('{{t| a |b|c}}').pformat())

    def test_commented_repformat(self):
        s = '{{t\n    | a <!--\n -->| 2 = b\n    | 3 = c\n}}'
        self.assertEqual(s, parse(s).pformat())

    def test_dont_treat_parser_function_arguments_as_kwargs(self):
        """The `=` is usually just a part of parameter value.

        Another example: {{fullurl:Category:Top level|action=edit}}.
        """
        self.assertEqual(
            '{{#if:\n'
            '    true\n'
            '    | <span style="color:Blue;">text</span>\n'
            '}}',
            parse(
                '{{#if:true|<span style="color:Blue;">text</span>}}'
            ).pformat())

    def test_ignore_zwnj_for_alignment(self):
        self.assertEqual(
            '{{ا\n    | نیم\u200cفاصله       = ۱\n    |'
            ' بدون نیم فاصله = ۲\n}}',
            parse('{{ا|نیم‌فاصله=۱|بدون نیم فاصله=۲}}').pformat())

    def test_equal_sign_alignment(self):
        self.assertEqual(
            '{{t\n'
            '    | long_argument_name = 1\n'
            '    | 2                  = 2\n'
            '}}',
            parse('{{t|long_argument_name=1|2=2}}').pformat())

    def test_arabic_ligature_lam_with_alef(self):
        """'ل' + 'ا' creates a ligature with one character width.

        Some terminal emulators do not support this but it's defined in
        Courier New font which is the main (almost only) font used for
        monospaced Persian texts on Windows. Also tested on Arabic Wikipedia.
        """
        self.assertEqual(
            '{{ا\n    | الف = ۱\n    | لا   = ۲\n}}',
            parse('{{ا|الف=۱|لا=۲}}').pformat())

    def test_pf_inside_t(self):
        wt = parse('{{t|a= {{#if:I|I}} }}')
        self.assertEqual(
            '{{t\n'
            '    | a = {{#if:\n'
            '        I\n'
            '        | I\n'
            '    }}\n'
            '}}',
            wt.pformat())

    def test_nested_pf_inside_tl(self):
        wt = parse('{{t1|{{t2}}{{#pf:a}}}}')
        self.assertEqual(
            '{{t1\n'
            '    | 1 = {{t2}}{{#pf:\n'
            '        a\n'
            '    }}\n'
            '}}',
            wt.pformat())

    def test_html_tag_equal(self):
        wt = parse('{{#iferror:<t a="">|yes|no}}')
        self.assertEqual(
            '{{#iferror:\n'
            '    <t a="">\n'
            '    | yes\n'
            '    | no\n'
            '}}',
            wt.pformat())

    def test_pformat_tl_directly(self):
        self.assertEqual(
            '{{t\n'
            '    | 1 = a\n'
            '}}',
            Template('{{t|a}}').pformat())

    def test_pformat_pf_directly(self):
        self.assertEqual(
            '{{#iferror:\n'
            '    <t a="">\n'
            '    | yes\n'
            '    | no\n'
            '}}',
            ParserFunction('{{#iferror:<t a="">|yes|no}}').pformat())

    def test_function_inside_template(self):
        p = parse('{{t|{{#ifeq:||yes}}|a2}}')
        self.assertEqual(
            '{{t\n'
            '    | 1 = {{#ifeq:\n'
            '        \n'
            '        | \n'
            '        | yes\n'
            '    }}\n'
            '    | 2 = a2\n'
            '}}',
            p.pformat())

    def test_parser_template_parser(self):
        p = parse('{{#f:c|e|{{t|a={{#g:b|c}}}}}}')
        self.assertEqual(
            '{{#f:\n'
            '    c\n'
            '    | e\n'
            '    | {{t\n'
            '        | a = {{#g:\n'
            '            b\n'
            '            | c\n'
            '        }}\n'
            '    }}\n'
            '}}',
            p.pformat())

    def test_pfromat_first_arg_of_functions(self):
        self.assertEqual(
            '{{#time:\n'
            '    {{#if:\n'
            '        1\n'
            '        | y\n'
            '        | \n'
            '    }}\n'
            '}}',
            parse('{{#time:{{#if:1|y|}}}}').pformat())

    def test_pformat_pf_whitespace(self):
        ae = self.assertEqual
        ae(
            '{{#if:\n'
            '    a\n'
            '}}',
            parse('{{#if: a}}').pformat())
        ae(
            '{{#if:\n'
            '    a\n'
            '}}',
            parse('{{#if:a }}').pformat())
        ae(
            '{{#if:\n'
            '    a\n'
            '}}',
            parse('{{#if: a }}').pformat())
        ae(
            '{{#if:\n'
            '    a= b\n'
            '}}',
            parse('{{#if: a= b }}').pformat())
        ae(
            '{{#if:\n'
            '    a = b\n'
            '}}',
            parse('{{#if:a = b }}').pformat())

    def test_pformat_tl_whitespace(self):
        ae = self.assertEqual
        ae('{{t}}', parse('{{ t }}').pformat())
        ae(
            '{{ {{t}} \n'
            '    | a = b\n'
            '}}',
            parse('{{ {{t}}|a=b}}').pformat())

    def test_zwnj_is_not_whitespace(self):
        self.assertEqual(
            '{{#if:\n'
            '    \u200c\n'
            '}}',
            parse('{{#if:\u200c}}').pformat())

    def test_colon_in_tl_name(self):
        ae = self.assertEqual
        ae(
            '{{en:text\n'
            '    |text<!--\n'
            '-->}}',
            parse('{{en:text|text}}').pformat())
        ae(
            '{{en:text\n'
            '    |1<!--\n'
            ' -->|2<!--\n'
            '-->}}',
            parse('{{en:text|1|2}}').pformat())
        ae(
            '{{en:text\n'
            '    |1<!--\n'
            ' -->| 2=v <!--\n'
            '-->}}',
            parse('{{en:text|1|2=v}}').pformat())

    def test_parser_function_with_an_empty_argument(self):
        """The result might seem a little odd, but this is a very rare case.

        The code could benefit from a little improvement.

        """
        self.assertEqual(
            '{{#rel2abs:\n'
            '    \n'
            '}}',
            parse('{{ #rel2abs: }}').pformat())

    def test_pf_one_kw_arg(self):
        self.assertEqual(
            '{{#expr:\n'
            '    2  =   3\n'
            '}}',
            parse('{{#expr: 2  =   3}}').pformat(),
        )

    def test_pformat_inner_template(self):
        c, b, a = WikiText('{{a|{{b|{{c}}}}}}').templates
        self.assertEqual(
            '{{b\n'
            '    | 1 = {{c}}\n'
            '}}', b.pformat())

    def test_repformat(self):
        """Make sure that pformat won't mutate self."""
        ae = self.assertEqual
        s = '{{a|{{b|{{c}}}}}}'
        a, b, c = WikiText(s).templates
        ae(
            '{{a\n    | 1 = {{b\n        | 1 = {{c}}\n    }}\n}}',
            a.pformat())
        # Again:
        ae(
            '{{a\n    | 1 = {{b\n        | 1 = {{c}}\n    }}\n}}',
            a.pformat())

    def test_pformat_keep_separated(self):
        """Test that `{{ {{t}} }}` is not converted to `{{{{t}}}}`.

        `{{{{t}}}}` will be interpreted as a parameter with {} around it.

        """
        self.assertEqual('{{ {{t}} }}', WikiText('{{{{t}} }}').pformat())

    def test_deprecated_pprint(self):
        # noinspection PyDeprecation
        self.assertWarns(DeprecationWarning, WikiText('').pprint, '  ', True)

    def test_last_arg_last_char_is_newline(self):
        """Do not add comment_indent when it has no effect."""
        ae = self.assertEqual
        ae(
            '{{text\n    |{{#if:\n        \n    }}\n}}',
            WikiText('{{text|{{#if:}}\n}}').pformat())
        ae(
            '{{text\n'
            '    |{{text\n'
            '        |{{#if:\n'
            '            \n'
            '        }}\n'
            '<!--\n'
            ' -->}}\n'
            '}}', WikiText('{{text|{{text|{{#if:}}\n}}\n}}').pformat())
        ae(
            '{{text\n'
            '    |{{text\n'
            '        |{{#if:\n'
            '            \n'
            '        }}\n'
            '    }}\n'
            '}}', WikiText('{{text|{{text|{{#if:}}\n    }}\n}}').pformat())
        ae(
            '{{text\n    |a\n    |b\n}}',
            WikiText('{{text|a\n    |b\n}}').pformat())
        ae(
            '{{text\n    |a\n    | 2 = b\n}}',
            WikiText('{{text|a\n    |2=b\n}}').pformat())
        ae(
            '{{en:text\n'
            '    | n=v\n'
            '}}', parse('{{en:text|n=v\n}}').pformat())

    def test_no_error(self):
        # the errors were actually found in shrink/insert/extend
        ae = self.assertEqual
        ae(
            parse('{{#f1:{{#f2:}}{{t|}}}}').pformat(),
            '{{#f1:'
            '\n    {{#f2:'
            '\n        '
            '\n    }}{{t'
            '\n        | 1 = '
            '\n    }}'
            '\n}}')
        ae(
            parse('{{{{#t2:{{{p1|}}}}}{{#t3:{{{p2|}}}\n}}}}\n').pformat(),
            '{{ {{#t2:'
            '\n        {{{p1|}}}'
            '\n    }}{{#t3:'
            '\n        {{{p2|}}}'
            '\n    }} }}'
            '\n')


class Sections(TestCase):

    """Test the sections method of the WikiText class."""

    def test_grab_the_final_newline_for_the_last_section(self):
        wt = WikiText('== s ==\nc\n')
        self.assertEqual('== s ==\nc\n', wt.sections[1].string)

    def test_blank_lead(self):
        wt = WikiText('== s ==\nc\n')
        self.assertEqual('== s ==\nc\n', wt.sections[1].string)

    # Todo: Parser should also work with windows line endings.
    @expectedFailure
    def test_multiline_with_carriage_return(self):
        s = 'text\r\n= s =\r\n{|\r\n| a \r\n|}\r\ntext'
        p = parse(s)
        self.assertEqual('text\r\n', p.sections[0].string)

    def test_inserting_into_sections(self):
        ae = self.assertEqual
        wt = WikiText('== s1 ==\nc\n')
        s1 = wt.sections[1]
        wt.insert(0, 'c\n== s0 ==\nc\n')
        ae('== s1 ==\nc\n', s1.string)
        ae('c\n== s0 ==\nc\n== s1 ==\nc\n', wt.string)
        s0 = wt.sections[1]
        ae('== s0 ==\nc\n', s0.string)
        ae('c\n== s0 ==\nc\n== s1 ==\nc\n', wt.string)
        s1.insert(len(wt.string), '=== s2 ===\nc\n')
        ae(
            'c\n'
            '== s0 ==\n'
            'c\n'
            '== s1 ==\n'
            'c\n'
            '=== s2 ===\n'
            'c\n',
            wt.string)
        s3 = wt.sections[3]
        ae('=== s2 ===\nc\n', s3.string)

    def test_insert_parse(self):
        """Test that insert parses the inserted part."""
        wt = WikiText('')
        wt.insert(0, '{{t}}')
        self.assertEqual(len(wt.templates), 1)

    def test_subsection(self):
        ae = self.assertEqual
        a = parse('0\n== a ==\n1\n=== b ===\n2\n==== c ====\n3\n').sections[1]
        ae('== a ==\n1\n=== b ===\n2\n==== c ====\n3\n', a.string)
        a_sections = a.sections
        ae('', a_sections[0].string)
        ae('== a ==\n1\n=== b ===\n2\n==== c ====\n3\n', a_sections[1].string)
        b = a_sections[2]
        ae('=== b ===\n2\n==== c ====\n3\n', b.string,)
        # Sections use the same span object
        self.assertTrue(b.sections[1]._span is b._span)
        ae('==== c ====\n3\n', b.sections[2].string)

    def test_tabs_in_heading(self):
        """Test that insert parses the inserted part."""
        t = '=\tt\t=\t'
        self.assertEqual(str(parse(t).sections[1]), t)

    def test_deleting_a_section_wont_corrupt_others(self):
        z, a, b, c = parse('=a=\na\n==b==\nb\n==c==\nc').sections
        del b.string
        self.assertEqual(c.string, '==c==\nc')

    def test_section_templates(self):
        """section.templates returns templates only from that section."""
        ae = self.assertEqual
        templates = parse('{{t1}}\n==section==\n{{t2}}').sections[1].templates
        ae(len(templates), 1)
        ae(templates[0].string, '{{t2}}')


class GetSection(TestCase):

    def test_by_heading_pattern(self):
        ae = self.assertEqual
        wt = parse(
            'lead\n'
            '= h1 =\n'
            '== h2 ==\n'
            't2\n'
            '=== h3 ===\n'
            '3\n'
            '= h =\n'
            'end'
        )
        lead, h1, h2, h3, h = wt.get_sections(include_subsections=False)
        ae(lead.string, 'lead\n')
        ae(h1.string, '= h1 =\n')
        ae(h2.string, '== h2 ==\nt2\n')
        ae(h3.string, '=== h3 ===\n3\n')
        ae(h.string, '= h =\nend')
        # return the same span when returning same section
        lead_, h1_, h2_, h3_, h_ = wt.get_sections(include_subsections=False)
        ai = self.assertIs
        ai(lead._span, lead_._span)
        ai(h._span, h_._span)
        # do not create repeated spans
        ae(len(wt._type_to_spans['Section']), 5)
        h1, h = wt.get_sections(include_subsections=False, level=1)
        ae(h1.string, '= h1 =\n')
        ae(h.string, '= h =\nend')


class WikiList(TestCase):

    def test_get_lists_with_no_pattern(self):
        ae = self.assertEqual
        wikitext = '*a\n;c:d\n#b'
        parsed = parse(wikitext)
        with self.assertWarns(DeprecationWarning):
            lists = parsed.lists()
        ae(len(lists), 3)
        ae(lists[1].items, ['c', 'd'])

    def test_multiline_tags(self):
        ae = self.assertEqual
        i1, i2, i3 = parse(
            '#1<br\n/>{{note}}\n#2<s\n>s</s\n>\n#3').get_lists()[0].items
        ae(i1, '1<br\n/>{{note}}')
        ae(i2, '2<s\n>s</s\n>')
        ae(i3, '3')
        # an invalid tag name containing newlines will break the list
        ae(len(parse('#1<br/\n>\n#2<abc\n>\n#3').get_lists()[0].items), 2)


class Tags(TestCase):

    def test_assume_that_templates_do_not_exist(self):
        # this is actually an invalid <s> tag on English Wikipedia, i.e the
        # result of {{para}} makes it invalid.
        self.assertEqual(len(parse('<s {{para|a}}></s>').get_tags('s')), 1)

    def test_unicode_attr_values(self):
        ae = self.assertEqual
        wikitext = (
            'متن۱<ref name="نام۱" group="گ">یاد۱</ref>\n\n'
            'متن۲<ref name="نام۲" group="گ">یاد۲</ref>\n\n'
            '<references group="گ"/>')
        parsed = parse(wikitext)
        with self.assertWarns(DeprecationWarning):
            ref1, ref2 = parsed.tags('ref')
        ae(ref1.string, '<ref name="نام۱" group="گ">یاد۱</ref>')
        ae(ref2.string, '<ref name="نام۲" group="گ">یاد۲</ref>')

    def test_defferent_nested_tags(self):
        ae = self.assertEqual
        parsed = parse('<s><b>strikethrough-bold</b></s>')
        b = parsed.get_tags('b')[0].string
        ae(b, '<b>strikethrough-bold</b>')
        s = parsed.get_tags('s')[0].string
        ae(s, '<s><b>strikethrough-bold</b></s>')
        s2, b2 = parsed.get_tags()
        ae(b2.string, b)
        ae(s2.string, s)

    def test_same_nested_tags(self):
        ae = self.assertEqual
        parsed = parse('<b><b>bold</b></b>')
        tags_by_name = parsed.get_tags('b')
        ae(tags_by_name[0].string, '<b><b>bold</b></b>')
        ae(tags_by_name[1].string, '<b>bold</b>')
        all_tags = parsed.get_tags()
        ae(all_tags[0].string, tags_by_name[0].string)
        ae(all_tags[1].string, tags_by_name[1].string)

    def test_self_closing(self):
        ae = self.assertEqual
        # extension tag
        ae(parse('<references />').get_tags()[0].string, '<references />')
        # HTML tag
        ae(parse('<s / >').get_tags()[0].string, '<s / >')

    def test_start_only(self):
        """Some elements' end tag may be omitted in certain conditions.

        An li element’s end tag may be omitted if the li element is immediately
        followed by another li element or if there is no more content in the
        parent element.

        See: https://www.w3.org/TR/html51/syntax.html#optional-tags
        """
        parsed = parse('<li>')
        tags = parsed.get_tags()
        self.assertEqual(tags[0].string, '<li>')

    def test_inner_tag(self):
        ae = self.assertEqual
        parsed = parse('<br><s><b>sb</b></s>')
        s = parsed.get_tags('s')[0]
        ae(s.string, '<s><b>sb</b></s>')
        b = s.get_tags()[1]
        ae(b.string, '<b>sb</b>')

    def test_extension_tags_are_not_lost_in_shadows(self):
        ae = self.assertEqual
        parsed = parse(
            'text<ref name="c">citation</ref>\n'
            '<references/>')
        ref, references = parsed.get_tags()
        ref.set_attr('name', 'z')
        ae(ref.string, '<ref name="z">citation</ref>')
        ae(references.string, '<references/>')

    def test_same_tags_end(self):
        self.assertEqual(
            WikiText('<s></s><s></s>').get_tags()[0]._span, [0, 7])


class Ancestors(TestCase):

    def test_ancestors_and_parent(self):
        ae = self.assertEqual
        parsed = parse('{{a|{{#if:{{b{{c<!---->}}}}}}}}')
        ae(parsed.parent(), None)
        ae(parsed.ancestors(), [])
        c = parsed.comments[0]
        c_parent = c.parent()
        ae(c_parent.string, '{{c<!---->}}')
        ae(c_parent.parent().string, '{{b{{c<!---->}}}}')
        ae(len(c.ancestors()), 4)
        ae(len(c.ancestors(type_='Template')), 3)
        ae(len(c.ancestors(type_='ParserFunction')), 1)
        t = Template('{{a}}')
        ae(t.ancestors(), [])
        self.assertIsNone(t.parent())

    def test_not_every_sooner_starting_span_is_a_parent(self):
        a, b = parse('[[a]][[b]]').wikilinks
        self.assertEqual(b.ancestors(), [])


if __name__ == '__main__':
    main()
