"""Variant 'modern': spelling and word division after the current German rules
(Marx' wording unchanged).

The word table (modern_map.json) comes from tools/mk_modern_map.py and
modern_overrides.py. Passages in other languages are left alone: a word counts
as foreign context when most of the words around it are foreign (list in
modern_map.json); a word also common in another language (Oct, Commission)
and an English possessive also when the words next to it are foreign. Words
the table knows as German only (not "foreign?") stay German, short ones (mass)
unless next to a foreign word. A few rewrites depend on context (Masse/Maße,
so lange/solange) or span several words (u. s. w. → usw., zu Grunde →
zugrunde).
"""

import json
import re
from collections import Counter
from pathlib import Path

from .modern_spots import COMMAS, EDGES, SPELLINGS

NAME = 'modern'
NOTICE = (
    'Orthographie, Getrennt- und Zusammenschreibung folgen den heutigen Regeln'
    ' (Wert statt Werth, Ware statt Waare, Prozess statt Process, Zirkulation'
    ' statt Cirkulation, produzieren statt produciren, groß statt gross, usw.'
    ' statt u. s. w., zugrunde statt zu Grunde, aufeinander statt auf einander,'
    ' jeder statt Jeder). Fehlende Kommas vor Nebensätzen und'
    ' Infinitivgruppen sind ergänzt, und das Komma nach einer Anführung oder'
    ' einem Einschub zwischen Gedankenstrichen steht hinter dem schließenden'
    ' Zeichen. Wortformen und Satzbau sind unverändert'
    ' (z. B. „andren“, „verschiedne“, „geschehn“, „ward“). Fremdsprachige Zitate,'
    ' Eigennamen und Titel bleiben in ihrer Schreibung, ebenso'
    ' frühneuhochdeutsche Zitate (Luther). Grundlage ist eine Wortliste aller'
    ' Formen der drei Bände mit Einzelentscheidungen.'
)

HERE = Path(__file__).resolve().parent
_DATA = json.load(open(HERE / 'modern_map.json', encoding='utf-8'))
MAP = {k: v[0] for k, v in _DATA['map'].items()}
FOREIGN = set(_DATA['foreign'])
AMBIGUOUS = {
    k for k, v in _DATA['map'].items() if v[1] == 'foreign?' or k in FOREIGN
}
GERMAN = {
    k for k, v in _DATA['map'].items() if v[1] in ('sz', 'word', 'compound')
} - FOREIGN
ORDINAL = {'st', 'nd', 'rd', 'th'}
TEI = '{http://www.tei-c.org/ns/1.0}'
BLOCKS = {
    TEI + t
    for t in (
        'p',
        'note',
        'head',
        'item',
        'cell',
        'l',
        'titlePart',
        'docImprint',
        'byline',
        'docAuthor',
        'trailer',
        'quote',
        'bibl',
        'fw',
        'label',
    )
}
BREAKS = {TEI + 'lb', TEI + 'pb'}
WORD = re.compile(
    r"[A-Za-zÄÖÜäöüßàâçéèêëîïôûùœæ]+(?:[’']s(?![A-Za-zÄÖÜäöüß]))?"
)
MASS_DAT = re.compile(
    r'(?:em|im|^demselben|^denselben|^selben|^gesellschaftlicher)$'
)
# "von neuem" after these nouns is an adjective (Bildung von neuem Kapital)
NEW_OF = set(
    'Zusetzen Zusatz Zufügung Anlage Vorschuss Produktion Bildung'
    ' Akkumulationsfonds Konkurrenz Schöpfung'.split()
)
CONTRACT = {
    'in',
    'auf',
    'an',
    'für',
    'durch',
    'um',
    'über',
    'vor',
    'unter',
    'hinter',
}
# Early New High German quotations (Luther etc.) keep their spelling
ENHG = {
    'hie',
    'kauffen',
    'bezalen',
    'Las',
    'rhümen',
    'nimpt',
    'Nehesten',
    'Nehisten',
    'stelen',
    'geschicht',
    'wolgetan',
    'Vernunfft',
    'sey',
    'seyn',
    'vierfaltiger',
    'Edelleut',
    'Kaufleut',
    'Leut',
    'geschazt',
    'Leiptzischen',
    'obs',
    'Machest',
    'Schadewacht',
    'itzt',
    'jtzt',
    'umb',
    'Gelt',
    'gelt',
    'hanget',
    'dieweil',
    'Dieweil',
    'kündten',
    'thubar',
    'jm',
    'jn',
    'jr',
    'sölch',
    'solchs',
    'Wucherer',
    'wuchern',
    'Pfarrherrn',
    'darumb',
    'warumb',
    'nicht',
    'eitel',
    'Gulden',
    'jeglichen',
    'Heiden',
    'drüber',
    'freilich',
    'jtzund',
    'itzund',
    'sonderlich',
    'thun',
    'thut',
    'vnd',
    'vnnd',
    'auff',
    'Teuffel',
    'Teufel',
    'lasst',
    'leihet',
    'verleihen',
}
ENHG_STRONG = {
    'hie',
    'kauffen',
    'bezalen',
    'rhümen',
    'nimpt',
    'Nehesten',
    'Nehisten',
    'geschicht',
    'wolgetan',
    'Vernunfft',
    'vierfaltiger',
    'Edelleut',
    'Kaufleut',
    'geschazt',
    'Leiptzischen',
    'Machest',
    'Schadewacht',
    'itzt',
    'jtzt',
    'umb',
    'hanget',
    'kündten',
    'thubar',
    'jm',
    'jn',
    'solchs',
    'darumb',
    'warumb',
    'jtzund',
    'itzund',
    'vnd',
    'vnnd',
    'auff',
    'Teuffel',
    'Leut',
    'sey',
    'obs',
    'stelen',
}

QUANT = (
    r'[\d½¼¾⅓]+.*|viele|einige|mehrere|verschiedliche|verschiedne|ganze|paar'
    r'|zwei|drei|vier|fünf|sechs|sieben|acht|neun|zehn|zwölf|hundert|tausend'
)
PHRASES = [
    (r'\bu\.\s?s\.\s?w\.', 'usw.'),
    (r'\bu\.\s?s\.\s?f\.', 'usf.'),
    (r'\bU\.\s?s\.\s?w\.', 'Usw.'),
    (r'\bu\.(\s?)A\.', r'u.\1a.'),
    (r'\b([Zz])\.(\s?)Th\.', r'\1.\2T.'),
    (r'\bgezähmten Thiers\b', 'gezähmten Tiers'),
    (r'\b([Ee])ben so\b', r'\1benso'),
    (
        (
            r'\b([Ii])rgend'
            r' (ein|eine|einen|einem|einer|eines|welche[mnrs]?'
            r'|wie|wo|etwas|jemand|wen|wer)\b'
        ),
        r'\1rgend\2',
    ),
    (r'\bzu Grunde\b', 'zugrunde'),
    (r'\bzu Gunsten\b', 'zugunsten'),
    (r'\bzu Ungunsten\b', 'zuungunsten'),
    (r'\bim Stande\b', 'imstande'),
    (r'\bzu Stande\b', 'zustande'),
    (r'\bin Stand (?=setz|gesetz|zu setz)', 'instand '),
    (r'\bin Folge dessen\b', 'infolgedessen'),
    (
        (
            r'\b([Ii])n Folge'
            r' (?=(der|des|dieser|dieses|seiner|ihrer|eines|einer|von)\b)'
        ),
        r'\1nfolge ',
    ),
    (r'\bstatt finde(t|n)\b', r'stattfinde\1'),
    (r'\bstatt fand(en)?\b', r'stattfand\1'),
    (r'\bstatt gefunden\b', 'stattgefunden'),
    (r'\bstatt zu finden\b', 'stattzufinden'),
    (r'\bStatt finde(t|n)\b', r'stattfinde\1'),
    (r'\bStatt fand(en)?\b', r'stattfand\1'),
    (r'\bStatt gefunden\b', 'stattgefunden'),
    (r'\bzu Teil (?=werd|wird|ward|wurd|geword)', 'zuteil '),
    (r'\b([Ss])o gar\b', r'\1ogar'),
    (r'\b([Ii])n (so|wie) ?(fern|weit)\b', r'\1n\2\3'),
    (r'\b([Ss])o fern\b', r'\1ofern'),
    (r'\b([Vv])or Allem\b', r'\1or allem'),
    (r'\bbei Seite\b', 'beiseite'),
    (r'\bzu Nutze\b', 'zunutze'),
    (r'\bzu Wege\b', 'zuwege'),
    (r'(?<!Tag )\bzu Tage\b', 'zutage'),
    (r'\bzu Statten\b', 'zustatten'),
    (r'\bvon [Ss]tatten\b', 'vonstatten'),
    (r'\b([Aa])n Statt\b', r'\1nstatt'),
    (r'\bzu Schulden\b', 'zuschulden'),
    (r'\b([Hh])eut zu Tage\b', r'\1eutzutage'),
    (r'\b([Nn])ichts desto (weniger|minder|trotz)\b', r'\1ichtsdesto\2'),
    (r'\b([Ss])o wohl (?=.{1,80}\bals\b)', r'\1owohl '),
    (
        (
            r'\b(auf|an|unter|durch|neben|nach|mit|für|gegen|von|zu|über'
            r'|aus|bei|hinter|in|vor|um)('
            r' )einander\b'
        ),
        r'\1einander',
    ),
    (
        (
            r'\b(Auf|An|Unter|Durch|Neben|Nach|Mit|Für|Gegen|Von|Zu|Über'
            r'|Aus|Bei|Hinter|In|Vor|Um)('
            r' )einander\b'
        ),
        r'\1einander',
    ),
    (r'\b([Ss])tatt dessen\b', r'\1tattdessen'),
    (r'\baußer Stande\b', 'außerstande'),
    (r'\b([Ss])o dass\b', r'\1odass'),
    (r'(^|[,;:(]\s*|[.!?]\s+)([Ss])o lange\b', r'\1\2olange'),
    (r'(^|[,;:(]\s*|[.!?]\s+)([Ss])o bald\b', r'\1\2obald'),
    (r'\b([Ii])n Folge\b', r'\1nfolge'),
    (r'\b([Ss])o zu sagen\b', r'\1ozusagen'),
    (r'\bvon vorn herein\b', 'von vornherein'),
    (r'\bheut zutage\b', 'heutzutage'),
    (r'\bTag ein,? Tag aus\b', 'tagein, tagaus'),
    (r'\bTag aus,? Tag ein\b', 'tagaus, tagein'),
    (r'\bJahr aus,? Jahr ein\b', 'jahraus, jahrein'),
    (r'\bWoche ein,? Woche aus\b', 'wochein, wochaus'),
    (r'\bHokus Pokus\b', 'Hokuspokus'),
    (r'\b([Bb])ei Leibe\b', r'\1eileibe'),
    (r'\bzu Liebe\b', 'zuliebe'),
    (r'\bzu Mute\b', 'zumute'),
    (r'\bin der That\b', 'in der Tat'),
    (r'\bStatt(?=[.,;:!?)])', 'statt'),
    (
        r'\b([Ss])o weit (?=(sie|er|es|sich|man|ich|wir|die|der|das|den|dem'
        r'|ein|eine|einer|nicht|dies|diese|dieser|sein|seine|ihr|ihre|nun'
        r'|übrigens)\b)',
        r'\1oweit ',
    ),
    (r'\b([Ss])oviel\b(?! (ich|wir|man)\b)', r'\1o viel'),
    (r'\b([Ss])oviele\b', r'\1o viele'),
    (r'\b([Ss])owenig\b', r'\1o wenig'),
    (r'\b([Zz])uviel\b', r'\1u viel'),
    (r'\b([Ww])ieviel\b', r'\1ie viel'),
    (r'\bWie Viel\b', 'Wieviel'),
    (r'\b([Ee])benso(wenig|viel|viele|gut|sehr|oft|lange)\b', r'\1benso \2'),
    (r'\b([Jj])emehr\b', r'\1e mehr'),
    (
        r'\b([Uu])m so (?=(?:mehr|weniger|eher|öfter|\w+er|\w+re[ns]?)\b)',
        r'\1mso ',
    ),
    (r'\b([Dd])em entsprechend', r'\1ementsprechend'),
    (r'\b([Ii])nfolge dessen\b', r'\1nfolgedessen'),
    (r'\balle dem\b', 'alledem'),
    (r'\bzu stande\b', 'zustande'),
    (r'\bhier zu Lande\b', 'hierzulande'),
    (r'\bsogut wie\b', 'so gut wie'),
    (r'\bTeil zu nehmen\b', 'teilzunehmen'),
    (r'(?<=[\d¼½¾⅓⅔]) mal\b(?! \d)', '-mal'),
    (r'\b(nicht|absolut) das geringste\b(?! [A-ZÄÖÜ])', r'\1 das Geringste'),
    (r'\b([Nn]icht) im geringsten\b(?! [A-ZÄÖÜ])', r'\1 im Geringsten'),
    (
        r'\baufs ([a-zäöüß]+ste)\b',
        lambda m: 'aufs ' + m.group(1).capitalize(),
    ),
    (r'\b([Jj])enachdem\b', r'\1e nachdem'),
    (r'\b([Uu])msomehr\b', r'\1mso mehr'),
    (r'\b([Nn])ichts destoweniger\b', r'\1ichtsdestoweniger'),
    (r'\b([Dd]as|dem) (eine|andre|andere)mal\b', r'\1 \2 Mal'),
    (
        r'\b([Zz]um|[Dd]as|[Dd]em|[Bb]eim)'
        r' (ersten|zweiten|dritten|letzten)mal\b',
        r'\1 \2 Mal',
    ),
    (r'\b([Jj])edesmal\b', r'\1edes Mal'),
    (r'\b([Bb])eidemal(e?)\b', lambda m: m.group(1) + 'eide Mal' + m.group(2)),
    (r'\bein für allemal\b', 'ein für alle Mal'),
    (r'\beine Zeitlang\b', 'eine Zeit lang'),
    (
        r'\b(\S+) (Jahre|Jahrzehnte|Jahrhunderte|Jahrtausende|Monate'
        r'|Wochen|Tage) lang\b',
        lambda m: (
            m.group(0)
            if re.fullmatch(QUANT, m.group(1))
            else m.group(1) + ' ' + m.group(2).lower() + 'lang'
        ),
    ),
    (
        r'\b(Uhr|Samstag|Sonntag|Montag) (Morgens|Abends|Nachmittags'
        r'|Vormittags|Mittags|Nachts)\b',
        lambda m: (
            m.group(1) + ' ' if m.group(1) == 'Uhr' else m.group(1).lower()
        )
        + m.group(2).lower(),
    ),
    (
        r'\b(Samstag|Sonntag|Montag) (Morgen|Abend|Nachmittag)\b',
        lambda m: m.group(1) + m.group(2).lower(),
    ),
    (
        r'(?<=[a-zäöüß0-9,;)] )(?<!des )(?<!eines )(?<!nächsten )'
        r'(?<!folgenden )(Nachts|Morgens|Abends|Vormittags|Nachmittags'
        r'|Freitags|Samstags|Sonnabends)\b',
        lambda m: m.group(1).lower(),
    ),
    (
        r'(?<!des )(?<!eines )(?<!dieses )\bAnfangs\b(?=\s*[^\sA-ZÄÖÜ-])',
        'anfangs',
    ),
    (
        r'(?<=[A-ZÄÖÜ][a-zäöüß]{2} )Namens\b'
        r'|(?<=[a-zäöüß]{4} )Namens(?= [A-Z])',
        'namens',
    ),
    (r'\bSeitens(?= (des|der|eines|einer)\b)', 'seitens'),
    (r'(?<!des )\bTags (?=(darauf|zuvor|vorher)\b)', 'tags '),
    (
        r"\b([A-Z][A-Za-zäöüé]*)[’'](sch(e|en|em|er|es)?)\b",
        lambda m: m.group(1)[0].lower() + m.group(1)[1:] + m.group(2),
    ),
    (
        r'\b(etwas|nichts|Etwas|Nichts) ((?:ganz|so|sehr|noch) )?'
        r'(?!(andres|anderes|andre|mehr|weniger|dies|des|eines)\b)'
        r'([a-zäöü][a-zäöü]+es)\b(?=\s*[^\sA-ZÄÖÜ])',
        lambda m: m.group(1)
        + ' '
        + (m.group(2) or '')
        + m.group(4)[0].upper()
        + m.group(4)[1:],
    ),
    (
        r'\b(das|dem|des|um das|ums|aufs) (doppelte|(?!einfach)\w+fache)'
        r'(n|s)?\b(?=\s*([.,;:)]|(der|des|von|vermehrt|gewachsen'
        r'|gestiegen)\b))',
        lambda m: m.group(1)
        + ' '
        + m.group(2)[0].upper()
        + m.group(2)[1:]
        + (m.group(3) or ''),
    ),
    (
        r'\b([Dd]as) ganze(?=[.,;:!?)]| (ist|war|wird|kömmt|kommt|bleibt'
        r'|besteht|hat|muss|sei|wäre)\b)',
        r'\1 Ganze',
    ),
    (
        r'\b([Ii]m) (allgemeinen|einzelnen|wesentlichen|ganzen|übrigen'
        r'|folgenden|besondern|besonderen|stillen|großen)\b'
        r'(?=\s*[^\sA-ZÄÖÜ])',
        lambda m: m.group(1) + ' ' + m.group(2)[0].upper() + m.group(2)[1:],
    ),
    (r'\bim voraus\b', 'im Voraus'),
    (r'\bwo andershin\b', 'woandershin'),
    (r'\banders woher\b', 'anderswoher'),
    (r'\bwo möglich noch\b', 'womöglich noch'),
    (
        r'\b((?:[Uu]ng|[Gg])lücklich|pfiffig|möglich|billig|notwendig'
        r'|natürlich|begreiflich|eigentümlich|[Ss]onderbar)er Weise\b',
        r'\1erweise',
    ),
    (r'\b([Ii]m) Ganzen und großen\b', r'\1 Ganzen und Großen'),
    (r'\bdes folgenden:', 'des Folgenden:'),
    (r'\bmanchmal dreifache der\b', 'manchmal Dreifache der'),
    (r'\bohne weit(e?)res\b', r'ohne Weit\1res'),
    (r'\b([Bb])ei weitem\b', r'\1ei Weitem'),
    (r'\baufs neue\b(?! [A-ZÄÖÜ])', 'aufs Neue'),
    (r'\b([Vv]or|seit)( ganz)? kurzem\b', r'\1\2 Kurzem'),
    (r'\bgleichviel (?=[A-ZÄÖÜ]|variables|oder mehr)', 'gleich viel '),
    (r'\b(gleich|auf) Null\b', r'\1 null'),
    (r'\bSumma Summarum\b', 'Summa summarum'),
    (r',“', '“,'),
    (r'\bin Bar\b', 'in bar'),
    (r'\b([Dd])as einzige(?=, wa?s|, wor)', r'\1as Einzige'),
    (
        r'\b((?:Sonn|Mon|Diens|Donners|Frei|Sams)tag|Mittwoch) (Nacht|Abend)\b',
        lambda m: m.group(1) + m.group(2).lower(),
    ),
    (
        r'\b([DdSs])(reißig|ieben)(jährige[nr]?) (?=Kriegs?\b)',
        lambda m: m.group(1).upper() + m.group(2) + m.group(3) + ' ',
    ),
    (r'(?<=[\d¼½¾⅓⅔]) ?(?=(?:stündig|jährig|tägig|pfündig)\w*\b)', '-'),
    (
        r'((?:\b(?:und|oder) |, )-)([A-ZÄÖÜ])(?=[a-zäöü])',
        lambda m: m.group(1) + m.group(2).lower(),
    ),
    (r'(?<=[a-zäöüß.])…', ' …'),
    (r'…(?=[A-ZÄÖÜa-zäöü])', '… '),
    (r'(?<=\b1[78]\d\d) :(?= )', ':'),
    (r'\b(im ersten|identischer) Act\b', r'\1 Akt'),
    (r'\b(sparsamer|den) Wirth\b', r'\1 Wirt'),
    (r'\b(ihr|zum|und) Thor\b', r'\1 Tor'),
    (r'\bWarenmasse entspringt\b', 'Warenmaße entspringt'),
    (
        r'\bbestimmte Masse (?=festgeronnener|der Warenarten|des Goldes)',
        'bestimmte Maße ',
    ),
    (r'\bden Ausfall gut machen\b', 'den Ausfall gutmachen'),
    (r'\bdass sie nicht gut gemacht\b', 'dass sie nicht gutgemacht'),
    (r'\bVerluste gut zu machen\b', 'Verluste gutzumachen'),
    (r'\bzu gute? kommt\b', 'zugutekommt'),
    (r'\bzu gut käme\b', 'zugutekäme'),
    (r'\b(Erfahrungen|darin) zu gut\b', r'\1 zugute'),
    (
        r'\baufrecht (erhalten|zu erhalten)\b',
        lambda m: 'aufrecht' + m.group(1).replace(' ', ''),
    ),
    (
        r'\b(auseinander|durcheinander|gegenüber|entgegen|zusammen|brach'
        r'|still|nieder|vorweg|vorlieb|kund|klar|heraus|hinaus|hinein|zurück'
        r'|dazwischen|sicher|fertig|kennen|weiter|wieder) (fallen|gesetzt|hält'
        r'|zu halten|zu setzenden|geworfen|gewürfelt|werfen|wirft|zu mischen'
        r'|zu wirren|zu würfeln|laufenden|gestellt|getreten|stellt|treten'
        r'|zu stellen|tritt|genommen|zu drängen|zu fallen|zu faseln|zu kommen'
        r'|gelegt|liegen|liegt|läge|setzt|zu setzen|zu stehn|gestanden'
        r'|gekniet|zu nehmen|zu tun|zu legen|machen|zu machen|macht'
        r'|zu ziehn|zu verlängern|zu werfen|zu lesen|erhalten|erhält|kommt'
        r'|kömmt|bringen|bringt|gebracht|zu bringen|gestellten|gelernt'
        r'|geführt|zu führen|hergestellt|hergestellten|herstellen|herstellt'
        r'|herzustellen|gewinnen|gekommen)\b',
        lambda m: _join(m),
    ),
]

# commas by today's rules
SUB = (
    r'dass|ob|wenn(?! auch| möglich)|weil|obgleich|obwohl|indem|sobald|nachdem'
    r'|bevor|ehe'
    r'|wo(?! möglich)|worin|womit|wovon|woraus|worauf|wodurch|wofür|wonach'
    r'|woran|worüber|wozu|wogegen'
)
NO_COMMA = set(
    'und oder aber sondern denn als wie so auch nur selbst schon noch erst'
    ' zwar gerade grade eben ja doch dass ob wenn weil also nämlich nicht'
    ' bloß statt anstatt ohne ohn außer außerdem trotzdem dadurch bis teils'
    ' einesteils zugleich ebenso endlich namentlich einerseits andrerseits'
    ' andererseits vielmehr besonders erstens zweitens drittens entweder'
    ' hauptsächlich zunächst vielleicht nie ebenfalls die der das welche'
    ' lange kurz gleich jedenfalls je sowohl ebensowohl sonst freilich meist'
    ' sodass während oft verkaufs sich mehr weniger viel'.split()
)
NO_COMMA_BEFORE = {
    'bevor': {'monate', 'monat', 'jahre', 'zeit'},
    'ehe': {'monate', 'monat', 'jahre', 'zeit'},
    'wovon': {'von', 'auf', 'infolge', 'grund', 'grundlage', 'teil'},
    'wo': {'von'},
}
WORD_BEFORE = r'(?<![\w′£)])((?:[\w′]+[)£]?|£))( +)'
UM_VERBS = (
    'tun',
    'kümmern',
    'bekümmern',
    'drehen',
    'bewerben',
    'bringen',
    'kommen',
    'streiten',
    'bitten',
    'sorgen',
    'handeln',
    'kämpfen',
)
NO_INF = {'den', 'ihn', 'ihnen', 'einen', 'seinen', 'ihren', 'diesen', 'eben'}


def _comma(m):
    w, conj = m.group(1), m.group(3)
    if (
        re.search(r'(\d|^[a-z])\)$', w)
        or w.lower() in NO_COMMA
        or w.lower() in NO_COMMA_BEFORE.get(conj, ())
    ):
        return m.group(0)
    return w + ',' + m.group(0)[len(w) :]


def _comma_inf(m):
    conj, words, inf = m.group(3), m.group(5) or '', m.group(6)
    if not inf.endswith('n') or inf in NO_INF:
        return m.group(0)
    if conj == 'um' and (
        inf in UM_VERBS
        or re.match(
            r'(\d|[¼½¾⅓⅔]|so\b|die Hälfte|das \w*fache|mehr\b|weniger\b'
            r'|einen Fuß|ein \w+tel\b)',
            words,
        )
    ):
        return m.group(0)
    pron = re.match(r'(sich|sie|es|ihn|ihm|ihnen|mich|etwas)\b', words)
    if conj == 'statt' and not pron:
        return m.group(0)
    if (
        conj == 'ohne'
        and words
        and not pron
        and not (inf == 'werden' and re.fullmatch(r'\w+(t|en)', words))
    ):
        return m.group(0)
    return _comma(m)


SPOTS = dict(SPELLINGS + COMMAS)


def _spot(m):
    _log[(m.group(0), SPOTS[m.group(0)])] += 1
    return SPOTS[m.group(0)]


PHRASES += [
    (
        r'(?<!\w)(?:'
        + '|'.join(re.escape(a) for a in sorted(SPOTS, key=len, reverse=True))
        + r')(?!\w)',
        _spot,
    )
]
PHRASES += EDGES
PHRASES += [
    (WORD_BEFORE + r'(' + SUB + r')\b', _comma),
    (WORD_BEFORE + r'(sondern\b|d\. h\.)()', _comma),
    (
        WORD_BEFORE + r'(um|ohne|statt)( +(?=(?:([^,.;:!?()–„“]{0,80}?) )?zu'
        r' ([a-zäöüß]+)\b))',
        _comma_inf,
    ),
]
PHRASES = [(re.compile(p), r) for p, r in PHRASES]

# separable verbs written apart in the original, joined today (Duden)
JOIN = {
    'auseinander': {'fallen', 'gesetzt', 'hält', 'zu halten', 'zu setzenden'},
    'durcheinander': {
        'geworfen',
        'gewürfelt',
        'werfen',
        'wirft',
        'zu mischen',
        'zu wirren',
        'zu würfeln',
        'laufenden',
    },
    'gegenüber': {'gestellt', 'getreten', 'stellt', 'treten', 'zu stellen'},
    'entgegen': {'gestellt', 'tritt'},
    'zusammen': {
        'genommen',
        'zu drängen',
        'zu fallen',
        'zu faseln',
        'zu halten',
        'zu kommen',
    },
    'brach': {'gelegt', 'liegen', 'liegt', 'läge'},
    'still': {'gesetzt', 'setzt', 'zu setzen', 'zu stehn', 'gestanden'},
    'nieder': {'gekniet'},
    'vorweg': {'genommen'},
    'vorlieb': {'zu nehmen'},
    'kund': {'zu tun'},
    'klar': {'zu legen', 'machen', 'zu machen', 'macht'},
    'heraus': {'zu ziehn'},
    'hinaus': {'zu verlängern', 'zu werfen'},
    'hinein': {'zu werfen', 'zu lesen'},
    'zurück': {'zu werfen', 'erhalten', 'erhält'},
    'dazwischen': {'kommt', 'kömmt'},
    'sicher': {'gestellt'},
    'fertig': {
        'bringen',
        'bringt',
        'gebracht',
        'zu bringen',
        'gestellt',
        'gestellten',
        'zu stellen',
    },
    'kennen': {'gelernt'},
    'weiter': {'geführt', 'zu führen'},
    'wieder': {
        'hergestellt',
        'hergestellten',
        'herstellen',
        'herstellt',
        'herzustellen',
        'gewinnen',
        'gekommen',
    },
}


def _join(m):
    if m.group(2) not in JOIN.get(m.group(1), ()):
        return m.group(0)
    return m.group(1) + m.group(2).replace(' ', '')


# pronouns written with a capital in the original, lower case today (not at the
# start of a sentence,
# not as a noun after an article: „das Nichts“, „ein Etwas“)
PRON = re.compile(
    r'(?<=[a-zäöüß0-9,;)–]\s)'
    r'(Jeder|Jede|Jedes|Jedem|Jeden|Alle|Alles|Allen|Aller|Allem|'
    r'Andre|Andrer|Andres|Andren|Andern|Andere|Anderer|Anderes|Anderen|'
    r'Eine|Einer|Einem|Einen|Eines|Keiner|Niemand|Jemand|'
    r'Nichts|Etwas|Beide|Beiden|Beides|Beider|'
    r'Viele|Vielen|Vieler|Wenige|Wenigen|Weniger|Einige|Einigen|Einiges|'
    r'Manches|Meisten|Dasselbe|Derselbe|Diejenigen|Derer|Diesen|Diesem|'
    r'Jenen)\b'
)
# before a capital that begins a sentence or a numbered item
SENTENCE = re.compile(r'[.!?][“)]* – $|(?:^|[.!?])\) $|(?<![\w)])\w\) $')
NOUN_AFTER = {
    'Nichts': ('das', 'ein', 'dem', 'des', 'im', 'Das', 'Ein'),
    'Etwas': ('das', 'ein', 'dem', 'des', 'im', 'Das', 'Ein'),
    'Weniger': ('oder',),
}


def lower_pronouns(s, at=None):
    def low(m):
        before = s[max(0, m.start() - 8) : m.start()]
        if (
            at not in (None, m.start())
            or SENTENCE.search(before)
            or before.split()[-1:]
            and before.split()[-1] in NOUN_AFTER.get(m.group(1), ())
        ):
            return m.group(1)
        return m.group(1).lower()

    return PRON.sub(low, s)


_log = Counter()


def blocks(root):
    text = root.find(TEI + 'text')
    for e in text.iter():
        if isinstance(e.tag, str) and e.tag in BLOCKS:
            yield e


def segments(block):
    """(element, 'text'|'tail') pairs of a block in reading order, without
    nested blocks' content."""
    out = []

    def walk(e, top):
        if e.text:
            out.append((e, 'text'))
        for c in e:
            if isinstance(c.tag, str) and c.tag in BLOCKS:
                pass
            elif isinstance(c.tag, str):
                walk(c, False)
            if c.tail:
                out.append((c, 'tail'))

    walk(block, True)
    return out


def is_foreign(w):
    return len(w) > 1 and (w in FOREIGN or re.split("[’']", w)[0] in FOREIGN)


def foreign_flags(words):
    flags = []
    for i, w in enumerate(words):
        win = [x for x in words[max(0, i - 3) : i + 4] if len(x) > 1]
        f = sum(1 for x in win if is_foreign(x))
        flag = f * 2 > len(win)
        if flag and w in GERMAN:
            near = words[max(0, i - 1) : i] + words[i + 1 : i + 2]
            flag = len(w) < 6 and any(is_foreign(x) for x in near)
        flags.append(flag)
    for i, w in enumerate(words):
        if flags[i]:
            continue
        before, after = words[max(0, i - 2) : i], words[i + 1 : i + 3]
        if w in AMBIGUOUS:
            flags[i] = bool(
                before[-1:]
                and before[-1] in ORDINAL
                or any(
                    len(side) == 2 and all(is_foreign(x) for x in side)
                    for side in (before, after)
                )
                or w == 'that'
                and any(is_foreign(x) for x in after)
            )
        elif re.search("[’']s$", w) and is_foreign(w):
            flags[i] = any(is_foreign(x) for x in after)
    return flags


def map_word(w, prev, foreign, prev2=''):
    if foreign:
        return w
    if w == 'neuem' and prev == 'von' and prev2 not in NEW_OF:
        return 'Neuem'
    if w in ('Masse', 'masse') and prev and MASS_DAT.search(prev.lower()):
        return w[0] + 'aße'
    if w == 'Schmidt' and prev == 'einen':
        return 'Schmied'
    m = re.fullmatch(r"(\w+)([’'])s", w)
    if m:
        base, apo = m.group(1), m.group(2)
        if base.lower() in CONTRACT:
            return base + 's'
        if base[0].isupper() and len(base) > 1:
            base = MAP.get(base, base)
            return base + apo if base[-1] in 'sxzß' else base + 's'
        return MAP.get(base, base) + apo + 's'
    return MAP.get(w, w)


def historic_quotes(text, offsets, flags):
    """Mark the words of „…“ quotations written in Early New High German."""
    for m in re.finditer(r'„[^“]{0,4000}?(?:“|$)', text):
        ws = WORD.findall(m.group(0))
        strong = sum(1 for w in ws if w in ENHG_STRONG)
        weak = sum(1 for w in ws if w in ENHG)
        if strong >= 2 or (strong and weak >= 4):
            for i, (a, b) in enumerate(offsets):
                if a >= m.start() and b <= m.end():
                    flags[i] = True


def modernize_text(s, foreign=None, before='', before2=''):
    """Plain string (formulas, headings in the config): word table + phrases,
    German context assumed."""
    words = WORD.findall(s)
    flags = foreign or [False] * len(words)
    it = iter(range(len(words)))
    prev = [before, before2]

    def rep(m):
        i = next(it)
        w = m.group(0)
        new = map_word(w, prev[0], flags[i], prev[1])
        prev[:] = w, prev[0]
        if new != w:
            _log[(w, new)] += 1
        return new

    s = WORD.sub(rep, s)
    if not any(flags):
        s2 = lower_pronouns(s)
        if s2 != s:
            _log[('Großschreibung Pronomen', 'klein')] += 1
            s = s2
    return apply_phrases(s)


def apply_phrases(s):
    for rx, r in PHRASES:
        s2 = rx.sub(r, s)
        if s2 != s:
            if r is not _spot:
                _log[(rx.pattern, str(r))] += 1
            s = s2
    return s


def phrases_across_lines(segs, foreign):
    """Phrases split by a line or page break: the rewritten phrase moves
    before the break."""
    segs = [
        (e, a)
        for e, a in segs
        if e.tag not in BREAKS or (getattr(e, a) or '').strip()
    ]
    for (e1, a1), (e2, a2) in zip(segs, segs[1:]):
        if e2.tag not in BREAKS or a2 != 'tail':
            continue
        t1, t2 = getattr(e1, a1) or '', e2.tail or ''
        lead = re.match(r'\s*', t2).group(0)
        m1 = re.search(r'\S(.*\S)?\s*$', t1, re.S)
        m2 = re.match(r'\S(.*\S)?', t2[len(lead) :], re.S)
        if not m1 or not m2:
            continue
        head, tail = m1.group(0).rstrip(), m2.group(0)
        both = head + ' ' + tail
        new = both
        if (e1, a1) not in foreign and (e2, a2) not in foreign:
            new = lower_pronouns(both, len(head) + 1)
        new = apply_phrases(new)
        if new == both:
            continue
        keep = 0
        while (
            keep < len(tail)
            and keep < len(new)
            and new[-1 - keep] == both[-1 - keep]
        ):
            keep += 1
        # not inside a word the phrase has joined across the break
        while keep and ' ' not in new[-keep - 1 : len(new) - keep + 1]:
            keep -= 1
        p = len(tail) - keep
        if p == 0 and not new[: len(new) - keep][-1:].isspace():
            p = 1
        while 0 < p < len(tail) and not tail[p - 1].isspace():
            p += 1
        keep = len(tail) - p
        cut = tail[p:].lstrip()
        moved = new[: len(new) - keep].rstrip()
        lead1 = t1[: m1.start()]
        if moved.startswith(',') and lead1.isspace():
            lead1, moved = ',' + lead1, moved[1:]
        setattr(e1, a1, lead1 + moved)
        e2.tail = lead + cut + t2[len(lead) + len(tail) :]


def transform(root, part):
    _log.clear()
    for b in blocks(root):
        segs = segments(b)
        texts = [getattr(e, a) for e, a in segs]
        joined, offsets, words, pos = '', [], [], 0
        for t in texts:
            for m in WORD.finditer(t):
                words.append(m.group(0))
                offsets.append((pos + m.start(), pos + m.end()))
            joined += t
            pos += len(t)
        flags = foreign_flags(words)
        historic_quotes(joined, offsets, flags)
        k, foreign = 0, set()
        for (e, a), t in zip(segs, texts):
            n = len(WORD.findall(t))
            if any(flags[k : k + n]):
                foreign.add((e, a))
            new = modernize_text(
                t,
                flags[k : k + n],
                words[k - 1] if k else '',
                words[k - 2] if k > 1 else '',
            )
            k += n
            if new != t:
                setattr(e, a, new)
        phrases_across_lines(segs, foreign)
    log = HERE.parent / 'build' / f'modern-changes-{part["key"]}.tsv'
    log.parent.mkdir(exist_ok=True)
    with open(log, 'w', encoding='utf-8') as f:
        for (old, new), n in sorted(
            _log.items(), key=lambda kv: (-kv[1], kv[0])
        ):
            f.write(f'{n}\t{old}\t{new}\n')


def _notice(s, quotes=False):
    """The editor's own words by the word table, quoted headings fully."""

    def sub(m):
        if m.group(0)[0] != '„':
            return MAP.get(m.group(0), m.group(0))
        return modernize_text(m.group(0)) if quotes else m.group(0)

    return re.sub(r'„[^“]*“|[A-Za-zÄÖÜäöüß]+', sub, s)


def adjust(vol):
    vol['title'] = modernize_text(vol['title']).replace(
        ')', ', heutige Rechtschreibung)'
    )
    vol['description'] = (
        modernize_text(
            vol.get('description', '').replace(
                ' Orthographie des Originals,', ''
            )
        )
        + ' Rechtschreibung nach heutigen Regeln.'
    )
    for key in ('structure', 'structure_epub', 'structure_pdf'):
        if key in vol:
            vol[key] = [_notice(s, True) for s in vol[key]]
    for key in ('pages_note', 'pages_note_pdf'):
        if key in vol:
            vol[key] = _notice(vol[key])
    if 'corrections' in vol:
        vol['corrections'] = [_notice(s) for s in vol['corrections']]
    vol['principle'] = (
        'Diese Ausgabe ist eine Leseausgabe der Erstausgabe in heutiger'
        ' Rechtschreibung. Sie gibt deren Wortlaut vollständig wieder und'
        ' berichtigt nur offensichtliche Fehler; alle Eingriffe sind im'
        ' Folgenden genannt.'
    )
    for part in vol['parts']:
        for key in ('toc_contents', 'part_label'):
            if key in part:
                part[key] = modernize_text(part[key])
        if part.get('formulas'):
            part['formulas'] = [
                (
                    f
                    if f.startswith('img:')
                    else re.sub(
                        r'(?<!\\)\b[A-Za-zÄÖÜäöüß]{2,}\b',
                        lambda m: MAP.get(m.group(0), m.group(0)),
                        f,
                    )
                )
                for f in part['formulas']
            ]
        for key in ('toc_fixes',):
            if part.get(key):
                part[key] = [
                    (modernize_text(a), modernize_text(b)) for a, b in part[key]
                ]
        if part.get('toc_skip'):
            part['toc_skip'] = tuple(
                modernize_text(s) for s in part['toc_skip']
            )
        if part.get('toc_title'):
            part['toc_title'] = modernize_text(part['toc_title'])
