import sys, os
root = os.path.abspath(os.path.join('server', '..'))
print('root', root)
print('exists app', os.path.exists(os.path.join(root, 'server', 'app.py')))
print('server dir exists', os.path.exists(os.path.join(root, 'server')))
print('before in sys.path', root in sys.path)
sys.path.insert(0, root)
print('after in sys.path', root in sys.path)
try:
    import server
    print('server module', server.__file__)
except Exception as e:
    print('import server failed', type(e), e)
