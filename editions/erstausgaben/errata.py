"""Corrections beyond the DTA transcription: the lists "Störende Druckfehler"
(Bd. 1, 1867) and "Druckfehler" (Bd. 3, 1894), obvious misprints in Greek
quotations, and (K1_TEXT) transcription errors and obvious misprints found by
comparing Bd. 1 with MEGA² II/5 (1983); K2_TEXT, K31_TEXT, K32_TEXT likewise for
Bd. 2 and 3 with MEGA² II/13 and II/15. MEGA served only as a pointer; doubtful
readings were checked against the facsimile. MEGA's factual corrections (names,
dates, page references, quotations adjusted to their sources) are not adopted.

The erratum for p. 534 ("Z. 11 v. o. lies 8 statt 11") matches nothing on that
page and is not applied. In Bd. 3 the erratum for p. I/115 (1857 for 1867) is
already in the DTA transcription.
"""

K1_ERRATA = [
    (
        'S. 39 Z. 1 v. o. setze ein vor unter',
        [
            (
                'Arbeitszeit ist daher unter<lb/>',
                'Arbeitszeit ist daher ein unter<lb/>',
            )
        ],
    ),
    (
        'S. 49 Z. 2 v. o. setze zu vor treten',
        [
            (
                'einander gegenübertreten. Solch',
                'einander gegenüberzutreten. Solch',
            )
        ],
    ),
    (
        'S. 63 Z. 6 v. u. wegzulassen: daraus entspringenden',
        [
            (
                'des Geldes, der daraus entspringenden verschiednen',
                'des Geldes, der verschiednen',
            )
        ],
    ),
    (
        'S. 64 Z. 17 v. u. Komma nach Werthmateriatur',
        [
            (
                'Werthmateriatur<lb/>\nGeld</hi>',
                'Werthmateriatur,<lb/>\nGeld</hi>',
            )
        ],
    ),
    (
        'S. 70 Z. 19 v. o. Punkt nach um',
        [
            (
                'Kornbranntwein um, G &#x2014; W, die',
                'Kornbranntwein um. G &#x2014; W, die',
            )
        ],
    ),
    (
        'S. 79 Z. 19 v. o. 1 Quarter Weizen statt 2 Quarters',
        [
            (
                'z. B. von 2 Quarter Weizen, 20 Ellen',
                'z. B. von 1 Quarter Weizen, 20 Ellen',
            )
        ],
    ),
    (
        'S. 82 Note Z. 1 wegzulassen in vor a nation',
        [('fail &#x2026; in a nation<lb/>', 'fail &#x2026; a nation<lb/>')],
    ),
    (
        'S. 103 Z. 13 v. o. setze von statt vom',
        [('Lokalformen vom Massstab', 'Lokalformen von Massstab')],
    ),
    (
        'S. 103 Z. 4 v. u. setze 13 statt 12',
        [('between one week and 12, then', 'between one week and 13, then')],
    ),
    (
        'S. 104 Note 90, Z. 5 v. o. lies: Gold und Silber',
        [('von Gold in Silber sieh', 'von Gold und Silber sieh')],
    ),
    (
        'S. 124 Z. 13 v. u. lies: noch statt nach',
        [('tion nach, unerklärlich', 'tion noch, unerklärlich')],
    ),
    (
        'S. 144 Z. 3 v. o. nach Stein einzuschalten Knochen',
        [
            (
                (
                    '<hi rendition="#g">Stein</hi> und <hi'
                    ' rendition="#g">Holz</hi> spielt'
                ),
                (
                    '<hi rendition="#g">Stein</hi>, <hi'
                    ' rendition="#g">Knochen</hi> und <hi'
                    ' rendition="#g">Holz</hi> spielt'
                ),
            )
        ],
    ),
    (
        'S. 160 Z. 15 v. u. lies ⅑ statt ⅓',
        [('ist um &#x2153; gewachsen', 'ist um &#x2151; gewachsen')],
    ),
    (
        'S. 276 Z. 3 v. o. lies Unmündiger',
        [('rechtlich Unmündige</hi>', 'rechtlich Unmündiger</hi>')],
    ),
    (
        "S. 292 Z. 4 v. o. fehlt nach b'b: in",
        [("Nimm an, b' b<lb/>", "Nimm an, b' b in<lb/>")],
    ),
    (
        'S. 403 Z. 4 v. u. lies 1821 statt 1812',
        [('Im Jahre 1812 betrug', 'Im Jahre 1821 betrug')],
    ),
    (
        'S. 417 Z. 15 v. u. nach was ist er wegzulassen',
        [('zu blasen, was er<lb/>', 'zu blasen, was<lb/>')],
    ),
    (
        'S. 554 Z. 15 v. u. „entzieht ihr“ statt „entzieht ihm“',
        [('zurück und entzieht ihm damit', 'zurück und entzieht ihr damit')],
    ),
    (
        'S. 611 Z. 15 v. u. wegzulassen „ist“',
        [
            (
                'cumulation ist. Die kontinuirliche',
                'cumulation. Die kontinuirliche',
            )
        ],
    ),
    (
        'S. 619 Z. 16 v. o. lies „waren“ statt „war“',
        [('räumbar war. Die plötzliche', 'räumbar waren. Die plötzliche')],
    ),
    (
        'S. 620 Z. 6 v. o. lies „einige“ und „überflüssige“',
        [
            (
                'Emigration einiger 100,000 überflüssiger',
                'Emigration einige 100,000 überflüssige',
            )
        ],
    ),
]
K1 = [f for _, fixes in K1_ERRATA for f in fixes]

K31_ERRATA = [
    (
        'S. 14 Z. 8 v. u. statt Verkäufer lies Käufer',
        [('erhält der Verkäufer 2', 'erhält der Käufer 2')],
    ),
    (
        'S. 21 Z. 3 v. o. statt x ℔ lies 12 x ℔',
        [
            (
                'in 12 Stunden x <hi rendition="#i">&#x2114;</hi>',
                'in 12 Stunden 12 x <hi rendition="#i">&#x2114;</hi>',
            )
        ],
    ),
    ('S. 50 Z. 2 v. o. statt 32.48 lies 33,27', [('= 32.48 %', '= 33,27 %')]),
    (
        'S. 158 Z. 15 v. o. statt warum lies worum',
        [('Centrum, warum sich', 'Centrum, worum sich')],
    ),
    (
        'S. 174 Z. 19 v. u. statt unterstellt lies unterstellen',
        [('Kapitals sind, unterstellt sie', 'Kapitals sind, unterstellen sie')],
    ),
    (
        'S. 180 Z. 17 v. u. statt 6 % lies 6⅔ %',
        [('eine Profitrate von 6 %', 'eine Profitrate von 6&#x2154; %')],
    ),
    (
        'S. 180 Z. 9 v. u. statt 6½ % lies 7 %',
        [('mehr als 6½ %', 'mehr als 7 %')],
    ),
    (
        (
            'S. 182 Z. 5–10 v. o. der Satz „Es ist klar … erhöht werden“ zu'
            ' streichen'
        ),
        [
            (
                (
                    ' Es ist klar,<lb/>\ndass wenn in Folge der Herstellung'
                    ' einer allgemeinen Profitrate<lb/>\nfür die Kapitale'
                    ' niedrer Zusammensetzung (wo v über dem'
                    ' Durch-<lb/>\nschnitt) die Werthe bei ihrer Verwandlung in'
                    ' Produktionspreise<lb/>\nherabgesenkt, sie für die'
                    ' Kapitale höherer Zusammensetzung er-<lb/>\nhöht'
                    ' werden.</p>'
                ),
                '</p>',
            )
        ],
    ),
    (
        'S. 205 Z. 10 v. o. statt Abnahme lies Zunahme',
        [('Möglichkeit der Abnahme der', 'Möglichkeit der Zunahme der')],
    ),
    (
        'S. 224 Z. 7 v. o. statt Rente lies Rate',
        [('die Rente des individuellen', 'die Rate des individuellen')],
    ),
    (
        'S. 224 Z. 8 v. o. statt Rate lies Rente',
        [('das Verhältniss der Rate zum', 'das Verhältniss der Rente zum')],
    ),
    (
        'S. 224 Z. 15 v. u. statt 12 % lies 13 %',
        [('auf 12 %. Die proportionelle', 'auf 13 %. Die proportionelle')],
    ),
    (
        'S. 239 Z. 6 v. o. statt einrichtet lies einrichten',
        [('Produktion einrichtet, nicht', 'Produktion einrichten, nicht')],
    ),
    (
        'S. 256 Z. 2 v. u. statt von lies vom',
        [('Kaufmann also von indu-', 'Kaufmann also vom indu-')],
    ),
    (
        'S. 262 Z. 2 v. u. statt Ramayr lies Ramsay',
        [('verwechselt Ramayr es', 'verwechselt Ramsay es')],
    ),
    (
        'S. 295 Z. 18 v. u. statt er lies es',
        [('er kommt immer mehr davon', 'es kommt immer mehr davon')],
    ),
    (
        'S. 352 Z. 13 v. o. statt ein lies kein',
        [('ist daher ein hand', 'ist daher kein hand')],
    ),
    (
        'S. 354 Z. 16 v. o. nach „Es ist“ ein Komma',
        [('wird. Es ist weil hier', 'wird. Es ist, weil hier')],
    ),
]
K31 = [f for _, fixes in K31_ERRATA for f in fixes]

K32_ERRATA = [
    (
        (
            'S. 51 Z. 13 v. u. lies: „und gleichzeitig steigt der Zinsfuss …'
            ' steigert ihren Preis“'
        ),
        [
            (
                (
                    'Geldkapital die steigende Nachfrage<lb/>\nnach'
                    ' Arbeitskraft vertheuert. Diese Waare wie jede andre'
                    ' steigert<lb/>\nihren Preis,'
                ),
                (
                    'Geldkapital. Die steigende Nachfrage<lb/>\nnach'
                    ' Arbeitskraft vertheuert diese Waare wie jede andre,'
                    ' steigert<lb/>\nihren Preis,'
                ),
            )
        ],
    ),
    (
        'S. 56 Z. 8 v. u. statt den lies dem',
        [('nach den Garn zu', 'nach dem Garn zu')],
    ),
    (
        'S. 94 Z. 19 v. u. hinter 12. Nov. 1857',
        [('am 12. Nov. war', 'am 12. Nov. 1857 war')],
    ),
    (
        'S. 95 Z. 5 v. o. statt 1847 lies 1844',
        [('Bankakt von 1847 die', 'Bankakt von 1844 die')],
    ),
    (
        'S. 148 Z. 15 v. o. statt der lies den',
        [('ihr der von euch mit Vor-', 'ihr den von euch mit Vor-')],
    ),
    (
        'S. 148 Z. 12 v. u. statt Oekonomie lies Oekonomen',
        [('tischen Oekonomie, besonders', 'tischen Oekonomen, besonders')],
    ),
    (
        'S. 306 Überschrift statt Achtundvierzigstes lies Sechsundvierzigstes',
        [
            (
                (
                    '<head><hi rendition="#g">Achtundvierzigstes'
                    ' Kapitel</hi>.<lb/>\n<hi rendition="#b">Baustellenrente.'
                ),
                (
                    '<head><hi rendition="#g">Sechsundvierzigstes'
                    ' Kapitel</hi>.<lb/>\n<hi rendition="#b">Baustellenrente.'
                ),
            )
        ],
    ),
]
K32 = [f for _, fixes in K32_ERRATA for f in fixes]

K1_GREEK = [
    ('&#x03F0;&#x03B1;&#x03BB;&#x03BF;&#x03C2;', 'καλὸς'),
    (
        '&#x03B1;&#x1F50;&#x03C4;&#x03B1;&#x03F1;'
        '&#x03F0;&#x03B5;&#x03AF;&#x03B1;',
        'αὐτάρκεια',
    ),
    ('&#x039A;&#x03BB;&#x03AF;&#x03BD;&#x03B1;&#x03B9;', 'Κλῖναι', 2),
    ('&#x03F0;&#x03BB;&#x03AF;&#x03BD;&#x03B1;&#x03B9;', 'κλῖναι'),
    ('&#x03BF;&#x1F36;&#x03BD;', 'οὖν'),
    ('&#x1F00;&#x03BB;&#x03B7;&#x03B4;&#x03B5;&#x03AF;&#x1FB3;', 'ἀληθείᾳ'),
]
K31_GREEK = [
    ('&#x03B1;&#x1F50;&#x03C4;&#x1FC6;', 'αὕτη'),
    (
        '&#x03B5;&#x03C0;&#x03AF;&#x03C3;&#x03C4;'
        '&#x03B1;&#x03C3;&#x03D1;&#x03B1;&#x03B9;',
        'ἐπίστασθαι',
        2,
    ),
    (
        '&#x03B5;&#x03C0;&#x03B9;&#x03C4;&#x03AC;'
        '&#x03C4;&#x03C4;&#x03B5;&#x03B9;&#x03BD;',
        'ἐπιτάττειν',
    ),
    ('&#x03C4;&#x03B1;&#x03C5;&#x03C4;&#x1F74;&#x03BD;', 'ταύτην'),
]

K1_TEXT = [
    ('oder aturalform', 'oder Naturalform'),
    ('gehört den Stäten', 'gehört den Städten'),
    ('zu kompensire</hi>', 'zu kompensiren</hi>'),
    ('seinem Werkzeng,', 'seinem Werkzeug,'),
    ('mensehlicher', 'menschlicher'),
    ('relativc', 'relative'),
    ('Känfers', 'Käufers'),
    ('realishten', 'realisirten'),
    ('selbsstständigen', 'selbstständigen'),
    ('Arheiter', 'Arbeiter'),
    ('Mebrarbeit', 'Mehrarbeit'),
    ('Verwerthungsbedüfniss', 'Verwerthungsbedürfniss'),
    ('dem Ak von', 'dem Akt von'),
    ('schcinbaren', 'scheinbaren'),
    ('selbststäudig', 'selbstständig'),
    ('Oceaus', 'Oceans'),
    ('lehendigen', 'lebendigen'),
    ('Werkzenge', 'Werkzeuge'),
    ('taglich', 'täglich'),
    ('selfácting', 'selfacting'),
    ('verhält-<lb/>\nmässig', 'verhältniss-<lb/>\nmässig'),
    ('Weith', 'Werth'),
    ('scin', 'sein'),
    ('Pfairei', 'Pfarrei'),
    ('Bedärfnisse', 'Bedürfnisse'),
    ('erláuben', 'erlauben'),
    ('Ver-<lb/>\nhaltniss', 'Ver-<lb/>\nhältniss'),
    ('Pricc', 'Price'),
    ('bébaut', 'bebaut'),
    ('hedarf', 'bedarf'),
    ('zerstrenten', 'zerstreuten'),
    ('Austanschbarkeit', 'Austauschbarkeit'),
    ('Acquivalente', 'Aequivalente'),
    ('Normaldaner', 'Normaldauer'),
    ('Produktionslarm', 'Produktionslärm'),
    ('abschwachte', 'abschwächte'),
    ('überprodueirt', 'überproducirt'),
    ('öffenbare', 'offenbare'),
    ('exproprürten', 'expropriirten'),
    ('Hie<lb/>\nRhodus', 'Hic<lb/>\nRhodus'),
    ('Themate', 'Themata'),
    ('Stenart', 'Steuart'),
    ('Litte-<lb/>\nrature', 'Lite-<lb/>\nrature'),
    ('distinetion', 'distinction'),
    ('labeur', 'labour'),
    ('labonr', 'labour'),
    ('Arbelt', 'Arbeit'),
    ('heurs', 'heures'),
    ('nöchsten', 'höchsten'),
    ('dehute', 'dehnte'),
    ('mésure', 'mesure'),
    ('ealled', 'called'),
    ('Konigreich', 'Königreich'),
    ('be-<lb/>\nrifft', 'bet-<lb/>\nrifft'),
    ('vicle', 'viele'),
    ('Prucksystem', 'Trucksystem'),
    ('Gedachtniss', 'Gedächtniss'),
    ('riniunione', 'riunione'),
    ('Buchezet', 'Buchez et'),
    ('Höhe unkt', 'Höhepunkt'),
    ('Christent um', 'Christenthum'),
    ('gleich-<lb/>\nbleib nden', 'gleich-<lb/>\nbleibenden'),
    ('ieder Hinsicht', 'jeder Hinsicht'),
    ('hand werksmässiger', 'handwerksmässiger'),
    ('unauf hörlich', 'unaufhörlich'),
    ('Schän<lb/>\ndung', 'Schän-<lb/>\ndung'),
    ('gesetzg ültig', 'gesetzgültig'),
    ('Go<lb/>\ndunof', 'Go-<lb/>\ndunof'),
    ('abge<lb/>\nrackert', 'abge-<lb/>\nrackert'),
    ('unter<lb/>\ndess', 'unter-<lb/>\ndess'),
    ('Aneignungs wei-<lb/>\nsen', 'Aneignungswei-<lb/>\nsen'),
    ('moile', 'moi le'),
    ('dueregard', 'due regard'),
    ('Werth-<lb/>\natomdarin', 'Werth-<lb/>\natom darin'),
    ('soweitihre', 'soweit ihre'),
    ('dermenschlichen', 'der menschlichen'),
    ('spieltletztrer', 'spielt letztrer'),
    ('pur-<lb/>\nposesaserf', 'pur-<lb/>\nposes a serf'),
    ('dis-<lb/>\ntinctvalues', 'dis-<lb/>\ntinct values'),
    ('dahinwiederum', 'dahin wiederum'),
    ('Punktam', 'Punkt am'),
    ('pastcenturies', 'past centuries'),
    ('Euro-<lb/>\npeansin', 'Euro-<lb/>\npeans in'),
    ('valeurà', 'valeur à'),
    ('quise', 'qui se'),
    ('dirigentle', 'dirigent le'),
    ('Brightet', 'Bright et'),
    ('oracomparative', 'or a comparative'),
    ('èmeedit', 'ème édit'),
    ('Rücken ausdrückt', 'Röcken ausdrückt'),
    ('folgenden Kapital sehn', 'folgenden Kapitel sehn'),
    ('längst den Land-<lb/>\nstrassen', 'längs den Land-<lb/>\nstrassen'),
    ('Versch&#x2019;eiss', 'Verschleiss'),
    ('dieN ation', 'die Nation'),
    ('dasWucherkapital', 'das Wucherkapital'),
    (
        'Comte&#x2019;sche Kom<lb/>\nbination',
        'Comte&#x2019;sche Kom-<lb/>\nbination',
    ),
    ('zum Eigen<lb/>\nthum', 'zum Eigen-<lb/>\nthum'),
    ('sinkt die<lb/>\nMass des', 'sinkt die<lb/>\nMasse des'),
    ('ihm genüge thut', 'ihm Genüge thut'),
    ('auch das Gold eine andre', 'auch das Geld eine andre'),
    ('Handwerke in eine Werkstatt', 'Handwerke in einer Werkstatt'),
    (
        'war nicht den Hollän-<lb/>\nder, sondern den Grund',
        'war nicht der Hollän-<lb/>\nder, sondern der Grund',
    ),
    ('mechanisches Ganze verbindet', 'mechanisches Ganzes verbindet'),
    ('früherer Moor', 'früheres Moor'),
    ('reine Kreatur der', 'reine Kreaturen der'),
    ('zehntägigen', 'zehnstündigen'),
    ('aus ihm gewinnen', 'aus ihm zu gewinnen'),
    (
        'galt nun<lb/>\n<hi rendition="#g">der Produktion',
        'galt nun<lb/>\n<hi rendition="#g">die Produktion',
    ),
    ('Eine bestimmtes', 'Ein bestimmtes'),
    ('depends of the', 'depends on the'),
    ('maintened', 'maintained'),
    ('abbondanemente', 'abbondantemente'),
    ('tsea', 'sea'),
    ('Kneetbrett', 'Knetbrett'),
    ('Adio', 'Addio'),
    ('Wandervölkerung', 'Wanderbevölkerung'),
    ('Gesellschallsorganisation', 'Gesellschaftsorganisation'),
    ('l&#x2019;atricier', 'Patricier'),
    ('also gesehn : In', 'also gesehn: In'),
    ('Lecture</hi> IlI.)', 'Lecture</hi> III.)'),
    ('Withoutstrength', 'Without strength'),
    ('the lead-<lb/>\ningarticle', 'the lead-<lb/>\ning article'),
    ('l c. p', 'l. c. p', 2),
    ('diese&#x201E;Missstände', 'diese &#x201E;Missstände'),
    ('edlen Metalle &#x201C;.</note>', 'edlen Metalle&#x201C;.</note>'),
    ('ertragen.&#x201E; Obsequium', 'ertragen. &#x201E;Obsequium'),
    (
        '<head>b) <hi rendition="#g">Widersprüche',
        '<head>2) <hi rendition="#g">Widersprüche',
    ),
]

K2_TEXT = [
    (
        '1000 II<hi rendition="#sub"><supplied>e</supplied></hi>',
        '1000 II<hi rendition="#sub">c</hi>',
    ),
    ('Richardo', 'Ricardo'),
    ('zusammmengebrachten', 'zusammengebrachten'),
    ('üsertrugen', 'übertrugen'),
    ('indnstriellen', 'industriellen'),
    ('verrrichtet', 'verrichtet'),
    (' dnrch ', ' durch '),
    ('Vorbereitungsstadinm', 'Vorbereitungsstadium'),
    ('Ausgangspnnkt', 'Ausgangspunkt'),
    ('Geschä&#x017F;t', 'Geschäft'),
    ('Kreislänfe', 'Kreisläufe'),
    ('Stocknng', 'Stockung'),
    ('dnrchläuft', 'durchläuft'),
    ('häuflg', 'häufig'),
    ('avous', 'avons'),
    ('kapitalistisehen', 'kapitalistischen'),
    (' Mafs ', ' Maß '),
    ('unbahängige', 'unabhängige'),
    ('Mafsstab', 'Maßstab'),
    ('dicsen', 'diesen'),
    ('Reichsthums', 'Reichthums'),
    ('Verkanfs', 'Verkaufs'),
    ('Klassifikatien', 'Klassifikation'),
    ('Werthttheil', 'Werththeil'),
    ('Bezng', 'Bezug'),
    ('Reparatureu', 'Reparaturen'),
    ('attes', 'altes'),
    ('audern', 'andern'),
    ('withont', 'without'),
    ('Bethandtheil', 'Bestandtheil'),
    ('Verchleiss', 'Verschleiss'),
    ('nieht', 'nicht'),
    ('Prodncenten', 'Producenten'),
    ('Besstimmung', 'Bestimmung'),
    ('\nletzre ', '\nletztre '),
    ('Werthschöpfang', 'Werthschöpfung'),
    ('Weun', 'Wenn'),
    ('Gröfse', 'Größe'),
    (' vielleich ', ' vielleicht '),
    ('Arbeitsperieden', 'Arbeitsperioden'),
    ('haupsächlich', 'hauptsächlich'),
    ('grofser', 'großer'),
    ('Umschlagsgechwindigkeit', 'Umschlagsgeschwindigkeit'),
    ('Àbkürzung', 'Abkürzung'),
    ('Mininum', 'Minimum'),
    ('Vorrähe', 'Vorräthe'),
    ('selhst', 'selbst'),
    ('hahe', 'habe'),
    ('Produktiensprocess', 'Produktionsprocess'),
    (' währen ', ' während '),
    ('Driitel', 'Drittel'),
    ('Ver-<lb/>\nläugerung', 'Ver-<lb/>\nlängerung'),
    ('Aulage', 'Anlage'),
    ('Produktionstoffe', 'Produktionsstoffe'),
    ('vor-<lb/>\ngeschossuen', 'vor-<lb/>\ngeschossnen'),
    ('denselbon', 'denselben'),
    ('Agrikultnr', 'Agrikultur'),
    (' sonder ', ' sondern '),
    ('sonddern', 'sondern'),
    ('Cirkulatfon', 'Cirkulation'),
    ('namentlieh', 'namentlich'),
    ('daes', 'dass'),
    ('Goldpro-<lb/>\ndnktion', 'Goldpro-<lb/>\nduktion'),
    ('gemäfses', 'gemäßes'),
    ('ausser-<lb/>\nv', 'ausser-<lb/>\n'),
    ('Produktionsproceses', 'Produktionsprocesses'),
    ('varschiedner', 'verschiedner'),
    (' edem ', ' jedem '),
    (' grofse ', ' große '),
    ('Lebensittel', 'Lebensmittel'),
    ('gleichmäfsig', 'gleichmäßig'),
    ('mafsgebend', 'maßgebend'),
    ('gauz', 'ganz'),
    ('falllende', 'fallende'),
    ('umgetzt', 'umgesetzt'),
    (' Kapitala ', ' Kapitals '),
    ('Prodnkte', 'Produkte'),
    ('kapi-<lb/>\nlistischer', 'kapita-<lb/>\nlistischer'),
    ('Sume', 'Summe'),
    ('Geschäftzweigs', 'Geschäftszweigs'),
    ('Labonring', 'Labouring'),
    ('Roproduktion', 'Reproduktion'),
    ('wiirkungslos', 'wirkungslos'),
    ('Botmälsigkeit', 'Botmäßigkeit'),
    ('beweisst', 'beweist'),
    ('konstantirter', 'konstatirter'),
    ('cirkulating', 'circulating'),
    ('hinzufügt', 'hinzugefügt'),
    ('shat', 'hat'),
    ('prés', 'près'),
    ('Reproduktionstheoríe', 'Reproduktionstheorie'),
    ('fixirt bleibendem Kapital', 'fixirt bleibenden Kapital'),
    ('derHand', 'der Hand'),
    ('th esame', 'the same'),
    ('Bestandtheiledes', 'Bestandtheile des'),
    ('andrerseitsals', 'andrerseits als'),
    ('sowohlsals', 'sowohl als'),
    ('j edes i Garn', 'jedes in Garn'),
    ('Funkti nen', 'Funktionen'),
    ('rückyerwandelten', 'rückverwandelten'),
    ('auch in dei Zeit', 'auch in der Zeit'),
    ('dieKasse', 'die Kasse'),
    ('ihrangehörigen', 'ihr angehörigen'),
    ('um gekehrte', 'umgekehrte'),
    ('rtir amortisirt', 'Er amortisirt'),
    ('Grofsen', 'Großen'),
    ('grofsen', 'großen'),
    ('miroirs oé les', 'miroirs où les'),
    ('in andrer Form (Waare)', 'in andre Form (Waare)'),
    ('in dem Kreislauf andrer', 'in den Kreislauf andrer'),
    ('Geldkapital, dass seinen Kreislauf', 'Geldkapital, das seinen Kreislauf'),
    ('als seinen Abkömmling', 'als seinem Abkömmling'),
    ('aus ihre Kapitalcharakter', 'aus ihrem Kapitalcharakter'),
    ('Geldkapital, dass<lb/>\nsich', 'Geldkapital, das<lb/>\nsich'),
    ('von fremden Geld', 'von fremdem Geld'),
    (
        'von produktiven Kapital<lb/>\nexistirenden',
        'von produktivem Kapital<lb/>\nexistirenden',
    ),
    ('in Lebensmittel zahlt', 'in Lebensmitteln zahlt'),
    ('dessen übrigen Werthelemente', 'dessen übrige Werthelemente'),
    ('das fixe Kapitel fortfährt', 'das fixe Kapital fortfährt'),
    ('bilden und ihm selbst', 'bilden und ihn selbst'),
    ('auf ihren Umschlag wird.', 'auf ihren Umschlag wirkt.'),
    (
        'und den flüs-<lb/>\nsigen Bestandtheil',
        'und der flüs-<lb/>\nsige Bestandtheil',
    ),
    ('in demselben Kapital (Book II', 'in demselben Kapitel (Book II'),
    (
        'zwi-<lb/>\nschen produktiven Kapital',
        'zwi-<lb/>\nschen produktivem Kapital',
    ),
    ('in Gold zurück', 'in Geld zurück'),
    ('dieses Kapitals für den Druck', 'dieses Kapitels für den Druck'),
    ('des Geschäft X', 'des Geschäfts X'),
    (
        (
            'des<lb/>\n<pb n="285" facs="#f0319"/>\nvorgeschossnen Kapital'
            ' angewandt'
        ),
        (
            'des<lb/>\n<pb n="285" facs="#f0319"/>\nvorgeschossnen Kapitals'
            ' angewandt'
        ),
    ),
    ('Quantum variables Kapitals', 'Quantum variablen Kapitals'),
    ('Realisation des Mehrwerth und', 'Realisation des Mehrwerths und'),
    (
        'innerhalb das Produktionsprocesses',
        'innerhalb des Produktionsprocesses',
    ),
    ('wonig Waare, im Unterschied', 'wenig Waare, im Unterschied'),
    (
        'wird, der Cha-<lb/>\nrakter seiner Anwendung',
        'wird, den Cha-<lb/>\nrakter seiner Anwendung',
    ),
    ('(nothwenigen und Luxus)', '(nothwendigen und Luxus)'),
    ('der nothwenigen Konsum', 'der nothwendigen Konsum'),
    ('dio', 'die'),
    ('Geld, dass die industriellen', 'Geld, das die industriellen'),
    ('nur in den Sinn', 'nur in dem Sinn'),
    (
        'mit seinem <hi rendition="#g">sach-<lb/>\nlichen</hi> Bestandtheilen',
        'mit seinen <hi rendition="#g">sach-<lb/>\nlichen</hi> Bestandtheilen',
    ),
    ('anf, dass die Produktionsmittel', 'auf, dass die Produktionsmittel'),
    ('ohne ihre andre Waare', 'ohne ihr andre Waare'),
    ('fixen Kapital transitorisch', 'fixen Kapitals transitorisch'),
    ('fortakkumu irt', 'fortakkumulirt'),
    ('darin, das er', 'darin, dass er'),
    ('moral schen', 'moralischen'),
    ('unter rationellen Konsum', 'unter rationellem Konsum'),
    ('unser<lb/>\nStahl', 'unsern<lb/>\nStahl'),
    ('aus gegenseitige<lb/>\nAustausch', 'aus gegenseitigem<lb/>\nAustausch'),
    ('existirt nicht nicht mehr', 'existirt nicht mehr'),
    ('fixem und<lb/>\nund flüssigem', 'fixem<lb/>\nund flüssigem'),
    ('variablem und<lb/>\nund konstantem', 'variablem<lb/>\nund konstantem'),
    ("P . , . W'", "P … W'"),
    ('Geldwerth von (1000', 'Geldwerth von 1000'),
    ('zn realisiren', 'zu realisiren'),
    ('dle einzelnen', 'die einzelnen'),
    ('dann = 600 <hi', 'dann = 6000 <hi'),
    ('Kapitalwerth im ihm', 'Kapitalwerth in ihm'),
]

K31_TEXT = [
    ('proportinal', 'proportional'),
    ('indentificirt', 'identificirt'),
    ('diesc', 'diese'),
    ('Hülfstoffen', 'Hülfsstoffen'),
    ('englicher', 'englischer'),
    ('Durchnittsalter', 'Durchschnittsalter'),
    ('Zasammen-<lb/>\nsetzung', 'Zusammen-<lb/>\nsetzung'),
    ('kapitalischen', 'kapitalistischen'),
    (' üher ', ' über '),
    ('Produk-<lb/>\nduktionsprocess', 'Pro-<lb/>\nduktionsprocess'),
    ('znrückgegeben', 'zurückgegeben'),
    ('Trausaktion', 'Transaktion'),
    ('zufallt', 'zufällt'),
    ('inter-<lb/>\nressirt', 'inte-<lb/>\nressirt'),
    ('Gegen-<lb/>\ngensatz', 'Ge-<lb/>\ngensatz'),
    (' Vorschusss ', ' Vorschuss '),
    ('blosssen', 'blossen'),
    ('Getreidethéurung', 'Getreidetheurung'),
    ('winkten', 'wirkten'),
    ('ver<lb/>\nsteht', 'ver<lb/>steht'),
    ('verkauf bar', 'verkaufbar'),
    ('nichtüberihrem', 'nicht über ihrem'),
    ('Ent<lb/>\nwicklung', 'Ent<lb/>wicklung'),
    ('vorallem', 'vor allem'),
    ('Güterererzeugung', 'Gütererzeugung'),
    ('thos epersons', 'those persons'),
    ('Rohproduktihrer', 'Rohprodukt ihrer'),
    ('links liegen and gehn', 'links liegen und gehn'),
    (
        'verkauft werden, dass heisst aber auch',
        'verkauft werden, das heisst aber auch',
    ),
    (
        'andrer<lb/>\nunter dem Werth sinken',
        'andrer<lb/>\nunter den Werth sinken',
    ),
    ('von 300 wird einem Profit', 'von 300 wird einen Profit'),
    (
        '2) einen<lb/>\nneu producirten Werth',
        '2) einem<lb/>\nneu producirten Werth',
    ),
    ('während ihm das bestimmte', 'während ihn das bestimmte'),
    ('dss', 'des'),
    (
        'und daher auch dem Produktionspreis',
        'und daher auch den Produktionspreis',
    ),
    ('gleichzeitig fallenden Profitrate', 'gleichzeitig fallender Profitrate'),
    ('zweitens der Profit hierauf', 'zweitens den Profit hierauf'),
    ('Realisirung der Werths', 'Realisirung des Werths'),
    ('unter diese beide Sorten', 'unter diese beiden Sorten'),
    ('Theilung das Bruttoprofits', 'Theilung des Bruttoprofits'),
    ('abgesehn vor aller', 'abgesehn von aller'),
    ('Caylay', 'Cayley'),
    ('Quarter ausländischer Weizens', 'Quarter ausländischen Weizens'),
    ('5 % und<lb/>\nund', '5 % und<lb/>'),
    ('Da da das Geschäft', 'Da das Geschäft'),
    ('Bereitung<lb/>\n(des Flachses in', 'Bereitung<lb/>\n(des Flachses) in'),
    ('von ie 100', 'von je 100'),
    (
        r'{200_c}</formula> + 100<hi rendition="#sub">v</hi>',
        r'{200_c + 100_v}</formula>',
    ),
    (
        r'{400_c}</formula> + 100<hi rendition="#sub">v</hi>',
        r'{400_c + 100_v}</formula>',
    ),
]

K32_TEXT = [
    ('Akkulumation', 'Akkumulation'),
    ('erhaltén', 'erhalten'),
    ('Geldkapitel', 'Geldkapital'),
    ('Leihkapitel', 'Leihkapital'),
    ('Ausszahlen', 'Auszahlen'),
    ('bevollmächtigté', 'bevollmächtigte'),
    ('ansübt', 'ausübt'),
    ('industriel-<lb/>\ndem', 'industriel-<lb/>\nlem'),
    ('vorkapitalischen', 'vorkapitalistischen'),
    ('farner', 'ferner'),
    ('Produktionsphäre', 'Produktionssphäre'),
    ('Unter-<lb/>\nnaltsmittel', 'Unter-<lb/>\nhaltsmittel'),
    ('naturwüchsigc', 'naturwüchsige'),
    ('natürwüchsige', 'naturwüchsige'),
    ('Ackerbauernte', 'Ackerbaurente'),
    ('vesteht', 'versteht'),
    ('Kapitanlalage', 'Kapitalanlage'),
    ('Arbeitlohns', 'Arbeitslohns'),
    (' zwische ', ' zwischen '),
    ('Gesammrental', 'Gesammtrental'),
    ('Gssammtkapital', 'Gesammtkapital'),
    ('Fruchtsbarkeitsgrade', 'Fruchtbarkeitsgrade'),
    ('Kapitatalanlage', 'Kapitalanlage'),
    ('hingekom-<lb/>\nkommen', 'hingekom-<lb/>\nmen'),
    ('Produktionkosten', 'Produktionskosten'),
    ('ent-<lb/>\nseheidend', 'ent-<lb/>\nscheidend'),
    ('Irrationallität', 'Irrationalität'),
    ('äberschüssige', 'überschüssige'),
    ('dureh', 'durch'),
    ('bisherign', 'bisherigen'),
    ('Jahrhnnderts', 'Jahrhunderts'),
    ('verkanft', 'verkauft'),
    ('ädaquatesten', 'adäquatesten'),
    ('gesellschaft-<lb/>\nlicken', 'gesellschaft-<lb/>\nlichen'),
    ('dieser dre<lb/>\nTheile', 'dieser drei<lb/>\nTheile'),
    ('Zusammenhaug', 'Zusammenhang'),
    ('zugesetzen', 'zugesetzten'),
    ('unwiderspiechlich', 'unwidersprechlich'),
    ('renonveler', 'renouveler'),
    ('Mehrwerts', 'Mehrwerths'),
    ('potentionelle', 'potentielle'),
    ('Fortschungstriebs', 'Forschungstriebs'),
    ('eine-<lb/>\nandre', 'eine -<lb/>\nandre'),
    ('Gedankenlosig<lb/>\nkeit', 'Gedankenlosig<lb/>keit'),
    ('niedergelegt, nnd zur', 'niedergelegt, und zur'),
    ('Aussage vou W. Newmarch', 'Aussage von W. Newmarch'),
    ('Zufuhren vou Edelmetall', 'Zufuhren von Edelmetall'),
    ('Chapmann', 'Chapman'),
    ('Currie &amp; Co.) von dem C. D.', 'Currie &amp; Co.) vor dem C. D.'),
    ('Warum es sich handelt', 'Worum es sich handelt'),
    ('\ndia ', '\ndie '),
    ('zu ihren parlamentarischen', 'zu ihrem parlamentarischen'),
    ('Hie<lb/>\nalso ist', 'Hier<lb/>\nalso ist'),
    (' werben,', ' werden,'),
    (
        'von besserm zu<lb/>\nschlechtern Boden',
        'von besserm zu<lb/>\nschlechterm Boden',
    ),
    ('Dis Natur der Sache', 'Die Natur der Sache'),
    ('in welchen auf Bodenarten', 'in welchem auf Bodenarten'),
    ('das Kapitel verdoppeln', 'das Kapital verdoppeln'),
    (
        'Zuschusskapitals bei konstantem oder fallenden Preis',
        'Zuschusskapitals bei konstantem oder fallendem Preis',
    ),
    (
        'mit konstantem und fallenden Preis',
        'mit konstantem und fallendem Preis',
    ),
    ('auf unterschiednem,<lb/>\nausser', 'auf unterschiednen,<lb/>\nausser'),
    (
        'mit den gewöhnlichen Profit anzulegen',
        'mit dem gewöhnlichen Profit anzulegen',
    ),
    ('Alle diesen falschen Ausflüchte', 'Alle diese falschen Ausflüchte'),
    ('ohne das irgend welcher', 'ohne dass irgend welcher'),
    (' dér<', ' der<'),
    (
        'gleichbleibenden Marktpreis die Masse',
        'gleichbleibendem Marktpreis die Masse',
    ),
    ('in free heads', 'in free hands'),
    ('nicht<lb/>\nmehr und nichts anders', 'nicht<lb/>\nmehr und nicht anders'),
    (
        'Krise, ihren<lb/>\nals übermächtige',
        'Krise, ihnen<lb/>\nals übermächtige',
    ),
    ('Form von Profit nnd Rente', 'Form von Profit und Rente'),
    ('Masse des Surplusprofits, resp-', 'Masse des Surplusprofits, resp.'),
    ('Suspension<lb/>\ndes Bankakts]', 'Suspension<lb/>\ndes Bankakts)'),
    ('wenn et sie', 'wenn er sie'),
    ('(Autstellung', '(Aufstellung'),
    ('gefäbrliche', 'gefährliche'),
    ('[der. Bankgesetzgebung]', '[der Bankgesetzgebung]'),
    ('Cirkulation<lb/>\nzn werfen', 'Cirkulation<lb/>\nzu werfen'),
    (
        (
            'beide (18 <hi rendition="#i">£</hi><lb/>\nund 36 <hi'
            ' rendition="#i">£</hi>.'
        ),
        (
            'beide (18 <hi rendition="#i">£</hi><lb/>\nund 36 <hi'
            ' rendition="#i">£</hi>).'
        ),
    ),
]
