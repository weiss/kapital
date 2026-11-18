"""DTA transcription errors in letter-spaced text (Sperrsatz), spot-checked
against the facsimile.

Word spaces are hard to see in spaced type: words run together or fall apart,
and the emphasis often starts one letter early ("Wert<hi>hgrösse" for
"Werth<hi>grösse"). Entries are raw_fixes.
"""

H = '<hi rendition="#g">'


def shift(pairs):
    """Move the start (a|b) or end (a/b) of an emphasis one letter right."""
    fixes = []
    for p, n in pairs:
        if '|' in p:
            a, b = p.split('|')
            fixes.append((a + H + b, a + b + H, n))
        else:
            a, b = p.split('/')
            fixes.append((a + '</hi>' + b, a + b + '</hi>', n))
    return fixes


K1 = [
    ('y Roc<hi rendition="#g">kwerth', 'y Rock <hi rendition="#g">werth'),
    ('Principes del&#x2019;Econ', 'Principes de l&#x2019;Econ'),
    ('fondamentaux del&#x2019;', 'fondamentaux de l&#x2019;'),
    ('quin&#x2019;a', 'qui n&#x2019;a'),
    ('Discours dela M', 'Discours de la M'),
    ('Sis<lb/>\nmondi', 'Sis-<lb/>\nmondi'),
    ('ganzent-<lb/>\ngegengesetzten', 'ganz ent-<lb/>\ngegengesetzten'),
    ('desrelativen', 'des relativen'),
    ('Gleichesbezieht', 'Gleiches bezieht'),
    ('bevorsie', 'bevor sie'),
    ('Geldist', 'Geld ist'),
    ('nurideelle', 'nur ideelle'),
    ('zweipolarisch', 'zwei polarisch'),
    ('forrais-<lb/>\ning', 'for rais-<lb/>\ning'),
    ('eachother', 'each other'),
    ('realisirtihren', 'realisirt ihren'),
    ('Werthpro-<lb/>\nduktseiner', 'Werthpro-<lb/>\ndukt seiner'),
    ('Verlänge-<lb/>\nrungdes', 'Verlänge-<lb/>\nrung des'),
    ('nurgrau-<lb/>\nsam', 'nur grau-<lb/>\nsam'),
    ('Wochearbeitet', 'Woche arbeitet'),
    ('Worksedit', 'Works edit'),
    ('therich', 'the rich'),
    ('Ab-<lb/>\nnahmein', 'Ab-<lb/>\nnahme in'),
    ('deMandeville', 'de Mandeville'),
    ('Arbeitselbst', 'Arbeit selbst'),
    ('Arbeitist', 'Arbeit ist'),
    ('dasabsolute', 'das absolute'),
    ('beschränktist', 'beschränkt ist'),
    ('drücktsich', 'drückt sich'),
    ('relativeSurpluspopulation', 'relative Surpluspopulation'),
    ('Erist', 'Er ist'),
    ('Anzahlarbei-<lb/>\ntender', 'Anzahl arbei-<lb/>\ntender'),
    ('Ueber-<lb/>\ngangaus', 'Ueber-<lb/>\ngang aus'),
    ('derur-<lb/>\nsprünglichen', 'der ur-<lb/>\nsprünglichen'),
    ('aufeigne', 'auf eigne'),
    ('dasser', 'dass er'),
    ('surleurs', 'sur leurs'),
    ('queleurs', 'que leurs'),
    ('welcheihren', 'welche ihren'),
    ('ihrverschiedenartigen', 'ihr verschiedenartigen'),
    ('aufsie', 'auf sie'),
    ('nichtihre', 'nicht ihre'),
    ('Naturalhautzum', 'Naturalhaut zum'),
    ('nichtschwer', 'nicht schwer'),
    ('zuihm', 'zu ihm'),
    ('ohnesolche', 'ohne solche'),
    ('Prozessesist', 'Prozesses ist'),
    ('woes', 'wo es'),
    ('talitself', 'tal itself'),
    ('all gemeines', 'allgemeines'),
    ('Formverschieden heit', 'Formverschiedenheit'),
    ('Beschäftigungs mittel', 'Beschäftigungsmittel'),
    ('Arbeiterbevöl kerung', 'Arbeiterbevölkerung'),
    ('abso lut', 'absolut'),
    ('Protektions system', 'Protektionssystem'),
    ('Arbeitsbeding ungen', 'Arbeitsbedingungen'),
    ('Unzertrennlich keit', 'Unzertrennlichkeit'),
] + shift(
    [
        ('Wert|h', 8),
        ('Leinwan|d', 5),
        ('Waare|n', 17),
        ('Arbeit|s', 1),
        ('Gel|d', 5),
        ('Zei|t', 1),
        ('Wohnung|s', 1),
        ('Roc|k', 2),
        ('Waare/n', 1),
        ('Wert/h', 1),
        ('Pächte/r', 1),
    ]
)

K2 = [
    ('fun giren', 'fungiren'),
] + shift(
    [('Arbeit|s', 1), ('Umschlag|s', 5), ('Produktion|s', 1), ('Wert/h', 1)]
)

K31 = [] + shift(
    [
        ('Wert|h', 1),
        ('Gel|d', 1),
        ('Produktion|s', 1),
        ('Mehrwerth|s', 1),
        ('Profi|t', 4),
        ('Kapita|l', 1),
    ]
)

K32 = [
    ('erzeu</hi>gt', 'erzeugt</hi>'),
] + shift([('Fruchtbarkeit|s', 1)])
