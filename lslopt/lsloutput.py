# Convert a symbol table (with parse tree) back to a script.
import lslfuncs
from lslcommon import Key, Vector, Quaternion

class outscript(object):

    # FIXME: is this correct:
    binary_operands = frozenset(('||','&&','^','|','&','==','!=','<','<=','>',
        '>=','<<','>>','+','-','*','/','%', '=', '+=', '-=', '*=', '/=','%=',
        ))
    extended_assignments = frozenset(('&=', '|=', '^=', '<<=', '>>='))
    unary_operands = frozenset(('NEG', '!', '~'))

    def Value2LSL(self, value):
        if type(value) in (Key, unicode):
            if type(value) == Key:
                # Constants of type key can not be represented
                raise lslfuncs.ELSLTypeMismatch
            return '"' + value.encode('utf8').replace('\\','\\\\').replace('"','\\"').replace('\n','\\n') + '"'
        if type(value) == int:
            return str(value)
        if type(value) == float:
            s = str(value)
            # Try to remove as many decimals as possible but keeping the F32 value intact
            exp = s.find('e')
            if ~exp:
                s, exp = s[:exp], s[exp:]
                if '.' not in s:
                    # I couldn't produce one but it's assumed that if it happens,
                    # this code deals with it correctly
                    return s + exp # pragma: no cover
            else:
                if '.' not in s:
                    # This should never happen (Python should always return a point or exponent)
                    return s + '.' # pragma: no cover
                exp = ''
            while s[-1] != '.' and lslfuncs.F32(float(s[:-1]+exp)) == value:
                s = s[:-1]
            return s + exp
        if type(value) == Vector:
            return '<' + self.Value2LSL(value[0]) + ', ' + self.Value2LSL(value[1]) \
                + ', ' + self.Value2LSL(value[2]) + '>'
        if type(value) == Quaternion:
            return '<' + self.Value2LSL(value[0]) + ', ' + self.Value2LSL(value[1]) \
                + ', ' + self.Value2LSL(value[2]) + ', ' + self.Value2LSL(value[3]) + '>'
        if type(value) == list:
            if value == []:
                return '[]'
            if len(value) < 5:
                return '[ ' + self.Value2LSL(value[0]) + ' ]'
            ret = '\n'
            first = True
            self.indentlevel += 1
            for entry in value:
                if not first:
                    ret += self.dent() + ', '
                else:
                    ret += self.dent() + '[ '
                ret += self.Value2LSL(entry) + '\n'
                first = False
            self.indentlevel -= 1
            return ret + self.dent() + self.indent + ']'
        raise lslfuncs.ELSLTypeMismatch

    def dent(self):
        return self.indent * self.indentlevel

    def OutIndented(self, code):
        if code[0] != '{}':
            self.indentlevel += 1
        ret = self.OutCode(code)
        if code[0] != '{}':
            self.indentlevel -= 1
        return ret

    def OutExprList(self, L):
        ret = ''
        if L:
            for item in L:
                if ret != '':
                    ret += ', '
                ret += self.OutExpr(item)
        return ret

    def OutExpr(self, expr):
        # Save some recursion by unwrapping the expression
        while expr[0] == 'EXPR':
            expr = expr[2]
        node = expr[0]

        if node == '()':
            return '(' + self.OutExpr(expr[2]) + ')'
        if node in self.binary_operands:
            return self.OutExpr(expr[2]) + ' ' + node + ' ' + self.OutExpr(expr[3])

        if node == 'IDENT':
            return expr[2]
        if node == 'CONSTANT':
            return self.Value2LSL(expr[2])
        if node == 'CAST':
            ret =  '(' + expr[1] + ')'
            expr = expr[2]
            if expr[0] == 'EXPR':
                expr = expr[2]
            if expr[0] in ('CONSTANT', 'IDENT', 'V++', 'V--', 'VECTOR',
                'ROTATION', 'LIST', 'FIELD', 'PRINT', 'FUNCTION', '()'):
                ret += self.OutExpr(expr)
            else:
                ret += '(' + self.OutExpr(expr) + ')'
            return ret
        if node == 'LIST':
            if len(expr) == 2:
                return '[]'
            return '[' + self.OutExprList(expr[2:]) + ']'
        if node == 'VECTOR':
            return '<' + self.OutExpr(expr[2]) + ', ' + self.OutExpr(expr[3]) \
                + ', ' + self.OutExpr(expr[4]) + '>'
        if node == 'ROTATION':
            return '<' + self.OutExpr(expr[2]) + ', ' + self.OutExpr(expr[3]) \
                + ', ' + self.OutExpr(expr[4]) + ', ' + self.OutExpr(expr[5]) + '>'
        if node == 'FUNCTION':
            return expr[2] + '(' + self.OutExprList(expr[3]) + ')'
        if node == 'PRINT':
            return 'print(' + self.OutExpr(expr[2]) + ')'

        if node in self.unary_operands:
            if node == 'NEG':
                node = '- '
            return node + self.OutExpr(expr[2])

        if node == 'FIELD':
            return self.OutExpr(expr[2]) + '.' + expr[3]

        if node in ('V--', 'V++'):
            return self.OutExpr(expr[2]) + node[1:]
        if node in ('--V', '++V'):
            return node[:-1] + self.OutExpr(expr[2])

        if node in self.extended_assignments:
            op = self.OutExpr(expr[2])
            return op + ' = ' + op + ' ' + node[:-1] + ' (' + self.OutExpr(expr[3]) + ')'

        raise Exception('Internal error: expression type "' + node + '" not handled') # pragma: no cover

    def OutCode(self, code):
        #return self.dent() + '{\n' + self.dent() + '}\n'
        node = code[0]
        if node == '{}':
            ret = self.dent() + '{\n'
            self.indentlevel += 1
            for stmt in code[2:]:
                ret += self.OutCode(stmt)
            self.indentlevel -= 1
            return ret + self.dent() + '}\n'
        if node == 'IF':
            ret = self.dent() + 'if (' + self.OutExpr(code[2]) + ')\n'
            ret += self.OutIndented(code[3])
            if len(code) > 4:
                ret += self.dent() + 'else\n'
                if code[4][0] == 'IF':
                    ret += self.OutCode(code[4])
                else:
                    ret += self.OutIndented(code[4])
            return ret
        if node == 'EXPR':
            return self.dent() + self.OutExpr(code) + ';\n'
        if node == 'WHILE':
            ret = self.dent() + 'while (' + self.OutExpr(code[2]) + ')\n'
            ret += self.OutIndented(code[3])
            return ret
        if node == 'DO':
            ret = self.dent() + 'do\n'
            ret += self.OutIndented(code[2])
            return ret + self.dent() + 'while (' + self.OutExpr(code[3]) + ');\n'
        if node == 'FOR':
            ret = self.dent() + 'for ('
            if code[2]:
                ret += self.OutExpr(code[2][0])
                if len(code[2]) > 1:
                    for expr in code[2][1:]:
                        ret += ', ' + self.OutExpr(expr)
            ret += '; ' + self.OutExpr(code[3]) + '; '
            if code[4]:
                ret += self.OutExpr(code[4][0])
                if len(code[4]) > 1:
                    for expr in code[4][1:]:
                        ret += ', ' + self.OutExpr(expr)
            ret += ')\n'
            ret += self.OutIndented(code[5])
            return ret
        if node == '@':
            return self.dent() + '@' + code[2] + ';\n'
        if node == 'JUMP':
            assert code[2][0:2] == ['IDENT', 'Label']
            return self.dent() + 'jump ' + code[2][2] + ';\n'
        if node == 'STATE':
            name = 'default'
            if code[2] != 'DEFAULT':
                assert code[2][0:2] == ['IDENT', 'State']
                name = code[2][2]
            return self.dent() + 'state ' + name + ';\n'
        if node == 'RETURN':
            if code[2] is None:
                return self.dent() + 'return;\n'
            return self.dent() + 'return ' + self.OutExpr(code[2]) + ';\n'
        if node == 'DECL':
            sym = self.symtab[code[3]][code[2]]
            ret = self.dent() + sym[1] + ' ' + code[2]
            if sym[2] is not None:
                ret += ' = ' + self.OutExpr(sym[2])
            return ret + ';\n'
        if node == ';':
            return self.dent() + ';\n'

        raise Exception('Internal error: statement type not found: ' + repr(node)) # pragma: no cover

    def OutFunc(self, typ, name, paramlist, paramsymtab, code):
        ret = self.dent()
        if typ is not None:
            ret += typ + ' '
        ret += name + '('
        first = True
        if paramlist:
            for name in paramlist:
                if not first:
                    ret += ', '
                ret += paramsymtab[name][1] + ' ' + name
                first = False
        return ret + ')\n' + self.OutCode(code)

    def output(self, symtab):
        # Build a sorted list of dict entries
        order = []
        self.symtab = symtab

        for i in symtab:
            item = []
            for j in sorted(i.items(), key=lambda k: -1 if k[0]==-1 else k[1][0]):
                if j[0] != -1:
                    item.append(j[0])
            order.append(item)

        ret = ''
        self.indent = '    '
        self.indentlevel = 0
        for name in order[0]:
            sym = symtab[0][name]

            ret += self.dent()
            if sym[1] == 'State':
                if name == 'default':
                    ret += 'default\n{\n'
                else:
                    ret += 'state ' + name + '\n{\n'

                self.indentlevel += 1
                eventorder = []
                for event in sorted(sym[2].items(), key=lambda k: k[1][0]):
                    eventorder.append(event[0])
                for name in eventorder:
                    eventdef = sym[2][name]
                    ret += self.OutFunc(eventdef[1], name, eventdef[3], symtab[eventdef[4]], eventdef[2])
                self.indentlevel -= 1
                ret += self.dent() + '}\n'

            elif len(sym) > 3:
                ret += self.OutFunc(sym[1], name, sym[3], symtab[sym[4]], sym[2])

            else:
                ret += sym[1] + ' ' + name
                if sym[2] is not None:
                    ret += ' = '
                    if type(sym[2]) == tuple:
                        ret += self.OutExpr(sym[2])
                    else:
                        ret += self.Value2LSL(sym[2])

                ret += ';\n'

        return ret