# Checkbox border has 36 black dots (at reportlab's native 72 dpi)

def translate(l, vec):
    return [l[0] + vec[0], l[1] + vec[1], l[2] + vec[0], l[3] + vec[1]]

def enlarge(l, percent):
    size = l[2] - l[0]
    ds = percent * size
    return [l[0] - 2*ds, l[1] - ds, l[2] + 2*ds, l[3] + ds]

def scale(l, c):
    return map(lambda x: c * x, l)

def transform(ll, translate_vector, scale_factor, enlarge_factor):
    for l in ll:
        l[:] = translate(l, translate_vector)
        l[:] = scale(l, scale_factor)
        l[:] = enlarge(l, enlarge_factor)
        l[:] = map(int, map(round, l))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
