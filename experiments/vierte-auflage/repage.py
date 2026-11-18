import rec, pickle, sys

pages = {}
for leaf in list(range(5, 37)) + list(range(37, 87)) + list(range(228, 303)):
    r = rec.parse_page(leaf)
    for tl in r['body'] + r['notes']:
        for t in tl:
            t['x'], t['s'] = rec.choose(t)
    pages[leaf] = r
pickle.dump(pages, open(f'{rec.W}/pages.pkl', 'wb'))
