import sys
sys.path.insert(0, r'c:\Users\sarab\.gemini\antigravity\scratch\SikhSituationBot')
print('root in sys.path', sys.path[0])
try:
    import server
    print('server import OK', server)
    print('server path', server.__file__)
except Exception as e:
    print('server import failed', type(e), e)
    import traceback; traceback.print_exc()
