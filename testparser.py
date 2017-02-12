#    (C) Copyright 2015-2016 Sei Lisa. All rights reserved.
#
#    This file is part of LSL PyOptimizer.
#
#    LSL PyOptimizer is free software: you can redistribute it and/or
#    modify it under the terms of the GNU General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    LSL PyOptimizer is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with LSL PyOptimizer. If not, see <http://www.gnu.org/licenses/>.

# Unit Testing of the optimizer, aiming for maximum coverage of the parser
# and of the optimization modules.

from lslopt.lslparse import parser,EParseSyntax,EParseUEOF,EParseAlreadyDefined,\
    EParseUndefined,EParseTypeMismatch,EParseReturnShouldBeEmpty,EParseReturnIsEmpty,\
    EParseInvalidField,EParseFunctionMismatch,EParseDeclarationScope,\
    EParseDuplicateLabel,EParseCantChangeState,EParseCodePathWithoutRet,fieldpos
from lslopt.lsloutput import outscript
from lslopt.lsloptimizer import optimizer
from lslopt import lslfuncs
import unittest
import os
import lslopt.lslcommon

class UnitTestCase(unittest.TestCase):
    pass

class Test01_LibraryLoader(UnitTestCase):
    def test_coverage(self):
        parser(builtins='builtins-unittest.txt')
        parser()


class Test02_Parser(UnitTestCase):
    def setUp(self):
        self.parser = parser()
        self.outscript = outscript()

    def test_coverage(self):
        try:
            os.remove('overwritten.lsl')
        except OSError:
            pass
        f = open('overwritten.lsl', 'wb')
        f.write('/*Autogenerated*/default{timer(){}}')
        f.close()
        del f
        self.parser.parsefile('overwritten.lsl')
        self.outscript.output(self.parser.parse("""default{touch(integer n){jump n;@n;}}"""))
        self.assertRaises(EParseUndefined, self.parser.parse, """default{touch(integer n){jump k;n;}}""")
        self.outscript.output(self.parser.parse("""default{touch(integer n){n;}}"""))
        print self.outscript.output(self.parser.parse(r"""string x="";
            vector V=ZERO_VECTOR;
            vector W = <1,2,3>;
            quaternion Q = <1,2,3,4>;
            float f;
            float ff = f;
            list L = [];
            list L2 = [2,3,4,5,-6];
            list L3 = [2,3,f,5,-6.0];
            rotation QQ = <f,f,f,f>;
            integer fn(integer x){
                if (1) for (f=3,f=4,f=5;3;f++,f++) do while(0); while(0); else if (2) return 2; else;
                fn(3);
                integer j = 3||4&&5|6^7&8.==9!=10.e+01f<11<=12>13.>=14<<15>>16== ++f+-f++;
                j *= 3.0; // LSL allows this
                1+((float)2+(integer)(1+1));
                12345678901;0x000000012345678901;0x000;
                2*(V*V/4)*V*--V.x*V.x++;
                L+L2;L+1;1+L;
                <0,0,0.>0>0>*<0,0,0==0>2,3>>3>3.>%<3,4,5>;
                f -= TRUE-(integer)-1;
                f *= !FALSE;
                V %= (ZERO_VECTOR+-ZERO_VECTOR)*(ZERO_ROTATION+-ZERO_ROTATION);
                1e37;1.1e22;1.;
                print(V *= 3);
                fwd("","","");
                L"\n\t\rxxxx";@lbl;jump lbl;
                {f;}
                [1,2,3];
                llOwnerSay((string)(L3+L2+QQ+Q+V+W+ff));
                return 1;
            }
            fwd(string a,string b,string c){}
            default{touch(integer n){n;state default;state another;return;}timer(){}}
            state another{timer(){}}//"""))
        self.assertRaises(EParseUEOF, self.parser.parse, '')
        self.assertRaises(EParseUEOF, self.parser.parse, 'default')
        self.assertRaises(EParseSyntax, self.parser.parse, 'x')
        self.outscript.output(self.parser.parse('integer x=TRUE;integer y=x;integer j=FALSE;default{timer(){}}'))
        self.assertRaises(EParseSyntax, self.parser.parse, ';')
        self.assertRaises(EParseSyntax, self.parser.parse, 'f(){}g(integer x,key y){{}}h(;){}')
        self.assertRaises(EParseSyntax, self.parser.parse, 'f(){}g(integer x,key y){}h()}')
        self.assertRaises(EParseUEOF, self.parser.parse, 'integer "')
        self.assertRaises(EParseSyntax, self.parser.parse, 'default{timer(){}}state blah{timer(){}}state ;')
        self.assertRaises(EParseSyntax, self.parser.parse, 'default{timer(integer x){}}')
        self.assertRaises(EParseSyntax, self.parser.parse, 'default{timer(integer x){(integer)x=0}}')
        self.assertRaises(EParseSyntax, self.parser.parse, 'default{timer(){state;}}')
        self.assertRaises(EParseAlreadyDefined, self.parser.parse, 'default{timer(integer x,integer x){}}')
        self.assertRaises(EParseSyntax, self.parser.parse, 'x;')
        self.assertRaises(EParseSyntax, self.parser.parse, '1e;')
        self.assertRaises(EParseSyntax, self.parser.parse, 'integer x=-TRUE;')
        self.assertRaises(EParseSyntax, self.parser.parse, 'integer x=-3;integer y=-x;')
        self.assertRaises(EParseAlreadyDefined, self.parser.parse, '''float x=3;float x;''')
        self.assertRaises(EParseAlreadyDefined, self.parser.parse, '''default{timer(){}}
            state blah{timer(){}}
            state blah{}''')
        self.assertRaises(EParseAlreadyDefined, self.parser.parse, '''default{timer(){@x;@x;}}''')
        self.assertRaises(EParseAlreadyDefined, self.parser.parse, '''default{timer(){integer x;@x;}}''')
        self.assertRaises(EParseAlreadyDefined, self.parser.parse, '''default{timer(){@x;integer x;}}''')
        self.assertRaises(EParseUEOF, self.parser.parse, 'float x=3+3;', set(('extendedglobalexpr',)))
        self.assertRaises(EParseUndefined, self.parser.parse, '''float x=-2147483648;float y=z;''')
        self.assertRaises(EParseUndefined, self.parser.parse, '''float z(){return 0;}float y=z;''')
        self.assertRaises(EParseUndefined, self.parser.parse, '''float y=z;float z;''')
        self.assertRaises(EParseUndefined, self.parser.parse, '''default{timer(){state blah;}}''')
        self.assertRaises(EParseUndefined, self.parser.parse, '''f(){k;}''')
        self.assertRaises(EParseReturnShouldBeEmpty, self.parser.parse, '''default{timer(){return 1;}}''')
        self.assertRaises(EParseReturnIsEmpty, self.parser.parse, '''integer f(){return;}''')
        self.assertRaises(EParseFunctionMismatch, self.parser.parse, '''f(integer i){f("");}''')
        self.assertRaises(EParseFunctionMismatch, self.parser.parse, '''f(integer i){f(1,2);}''')
        self.assertRaises(EParseFunctionMismatch, self.parser.parse, '''f(integer i){f(f(1));}''')
        self.assertRaises(EParseFunctionMismatch, self.parser.parse, '''f(integer i){f();}''')
        self.assertRaises(EParseDeclarationScope, self.parser.parse, '''f(){if (1) integer i;}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){[f()];}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){3.||2;}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){3||2.;}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){3.|2;}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){3|2.;}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){3.&2;}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){3&2.;}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){3.^2;}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){3^2.;}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){f()!=2;}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){2!=f();}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){3.<"";}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){""<"".;}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){3.<<2;}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){3>>2.;}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){""-(key)"";}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){""+f();}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){""+(key)"";}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){(key)""+"";}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){(key)""+(key)"";}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){key k;k+k;}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){3/<1,2,3>;}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){3/<1,2,3,4>;}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){""*3;}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){""%4;}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){3%<2,3,4>;}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){""%4;}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){float i;i%=2;}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){float i;i&=2;}''', ['extendedassignment'])
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){(vector)4;}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){key k;k+=k;}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){string i;i++;}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){string i;(i-=i);}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){string i;(i*=i);}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){string i;-i;}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){string i;~i;}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){string i;!i;}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){string i;++i;}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''g(){integer k;k=g();}''')
        self.assertRaises(EParseUndefined, self.parser.parse, '''g(){@x;x;}default{}state x{}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''g(){print(g());}default{}''')
        self.assertRaises(EParseUndefined, self.parser.parse, '''g(){integer k;k();}''')
        self.assertRaises(EParseUndefined, self.parser.parse, '''g(){++x;}state x{}''')
        self.assertRaises(EParseUndefined, self.parser.parse, '''g(){print(x);}state x{}''')
        self.assertRaises(EParseUEOF, self.parser.parse, '''f(){(integer)''')
        self.assertRaises(EParseInvalidField, self.parser.parse, '''f(){vector v;v.s;}''')
        self.assertRaises(EParseDuplicateLabel, self.parser.parse, 'f(){@x;{@x;}}')
        self.assertRaises(EParseCantChangeState, self.parser.parse, 'f(){state default;}default{}')
        self.assertRaises(EParseSyntax, self.parser.parse, '''f(){<1,2,3,4==5>;}''')
        self.assertRaises(EParseSyntax, self.parser.parse, '''#blah;\ndefault{timer(){}}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){<1,2,3,4>"">;}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){<1,2,3,"">"">;}''')
        self.assertRaises(EParseTypeMismatch, self.parser.parse, '''f(){string i;(i&=i);}''',
            set(('extendedassignment')))

        self.assertRaises(EParseUndefined, self.parser.parse, '''key a=b;key b;default{timer(){}}''',
            ['extendedglobalexpr'])
        # Force a list constant down its throat, to test coverage of LIST_VALUE
        self.parser.constants['LISTCONST']=[1,2,3]
        print self.outscript.output(self.parser.parse('default{timer(){LISTCONST;}}'))

        print self.outscript.output(self.parser.parse('''string s="1" "2";default{timer(){}}''',
            ['allowmultistrings'])) # the one below doesn't work because it uses extended global expr.
        print self.outscript.output(self.parser.parse('''
            float f=2+2;
            #blah;
            string s = "1" "2";
            list L = [(key)""];
            integer fn1(){if (1) {return 3;}else if (2)return 4; return 5;}
            integer fn2(){if (1) return 3; else if (2) return 4; else return 5;}
            default{timer(){
                1+([]+(integer)~1);
                list a;
                float f;
                a = (list)3; a += 3;
                f += 4; f += -4.3;
                integer i;
                i *= 1.3;
                i |= i;
                "a" "b" "c";
                "a"+(key)"b"; (key)"a" + "b";
                i>>=i; {@x;{@x;jump x;}jump x;}
            }}''',
            ['explicitcast','extendedtypecast','extendedassignment',
                'extendedglobalexpr', 'allowmultistrings', 'allowkeyconcat',
                'processpre', 'duplabels']
            ))
        print self.parser.scopeindex

        self.assertEqual(fieldpos("a,b", ",", 3), -1)
        self.assertEqual(self.outscript.Value2LSL(lslfuncs.Key(u'')), '((key)"")')
        self.assertRaises(AssertionError, self.outscript.Value2LSL, '')

    def test_regression(self):
        self.assertRaises(EParseCodePathWithoutRet, self.parser.parse,
            '''key f() { if (1) ; else if (2) return ""; else return ""; }''')
        self.parser.parse('f(){if(1) {state default;}if (1) if (1) state default; else state default;}default{timer(){}}')
        self.parser.parse('default{timer(){vector v;v.x=0;}}')

        # Check for exceptions only
        self.parser.parse('default{timer(){jump x;while(1)@x;}}')
        self.parser.parse('default{timer(){jump x;do@x;while(1);}}')
        self.parser.parse('default{timer(){jump x;for(;1;)@x;}}')
        self.parser.parse('default{timer(){jump x;while(1)@x;}}', ('breakcont',))
        self.parser.parse('default{timer(){jump x;do@x;while(1);}}', ('breakcont',))
        self.parser.parse('default{timer(){jump x;for(;1;)@x;}}', ('breakcont',))

        self.parser.parse('default{timer(){for(llDie();1;llDie());}}')

        self.assertRaises(EParseUndefined, self.parser.parse,
            'default{timer(){jump x;while(1){@x;}}}')
        self.assertRaises(EParseUndefined, self.parser.parse,
            'default{timer(){jump x;{while(1)@x;}}}')


    def tearDown(self):
        del self.parser
        del self.outscript

class Test03_Optimizer(UnitTestCase):
    def setUp(self):
        self.parser = parser()
        self.opt = optimizer()
        self.outscript = outscript()

    def test_coverage(self):
        p = self.parser.parse('''
            float f=2+llAbs(-2);
            float g = f;
            string s = "1" "2";
            list L = [(key)""];
            list L1 = L;
            list L2 = [1,2,3,4,5,6.0];
            list L3 = [];
            list L4 = [1,2,3,4,5,6.0,""]+[];
            integer RemovesInt = 0;
            vector AddsVector;
            vector v=<1,2,f>;
            float ffff2 = v.x;
            vector vvvv = <1,2,llGetNumberOfSides()>;
            float ffff=vvvv.x;
            vector vvvv2=vvvv;
            float ffff3 = v.z;
            integer fn(){
                if (1) state default; else return 2;
                return fn();}

            default{touch(integer n){
                1+([]+(integer)~1);
                list a;
                float f;
                vector v=<1,2,f>;<1,2,3>;<1,2,3,4>;v.x;
                v-<0,0,0>;<0,0,0>-v;v+<0,0,0>;<0,0,0>+v;
                []+f;
                integer j = 3||4&&5|6^7&8.==9!=10.e+01f<11<=12>13.>=14<<15>>16==0&&3==
                    ++f-f++-(3 + llFloor(f)<<3 << 32) - 2 - 0;
                integer k = 2 + (3 * 25 - 4)/2 % 9;
                a = (list)3; a += !3; a = 3+a;
                f += 4; f += -4.3;
                integer i;
                i = llGetListLength(L);
                if (i&&llSameGroup(llGetOwner())) ++i;
                i *= -3.0;
                print(3+2);
                i |= !i;
                llOwnerSay((string)(L3+L4+i+L2+L1+vvvv));
                "a" "b" "c";
                <2, 3, llSetRegionPos(<4,5,6>)>;
                "a"+(key)"b"; (key)"a" + "b";
                llOwnerSay(llUnescapeURL("%09"));
                i>>=i;
                if (1) do while (0); while (0); if (0); if (0);else; for(;0;);
                if (i) if (i); else ; while (i) ; do ; while (i); for(;i;);
                (i-i)+(i-3)+(-i+i)+(-i-i)+(i+1)+(-i+1)+(i-1)+(-i-1)+(0.0+i);
                ((-i)+j);((-i)+i);i-2;-i-2;2-i;
                for(i=3,i;1;){}
                if (1) state default; else ;
                do while (1); while(1); for(;1;);
                for (i=0,i;0;);for(i=0,i=0;0;);return;
            }}''',
            ['explicitcast','extendedtypecast','extendedassignment',
                'extendedglobalexpr', 'allowmultistrings', 'allowkeyconcat']
            )
        self.opt.optimize(p)
        self.opt.optimize(p,['optimize','shrinknames'])
        self.opt.optimize(p, ())
        print self.outscript.output(p)

        p = self.parser.parse('''string s = llUnescapeURL("%09");default{timer(){float f=llSqrt(-1);
            integer i;i++;i=i;-(-(0.0+i));!!(!~~(!(i)));[]+i+s+f;llOwnerSay(s);}}''',
            ['extendedtypecast', 'extendedassignment',
                'extendedglobalexpr', 'allowmultistrings', 'allowkeyconcat']
            )
        self.opt.optimize(p, ['optimize','foldtabs'])
        print self.outscript.output(p)

        p = self.parser.parse(
        '''integer i1; integer i2; integer i3; integer i4; integer i5;
        string s1; string s2; string s3; string s4; string s5;
        f1(){jump x; @x;} f2(){integer i3; i4=0; s3=""; f1();
        if (1) state another;}
        default { timer() { state another; } }
        state another { timer() { state default; } touch(integer num_det) {} }
        ''')
        self.opt.optimize(p, ['optimize','shrinknames'])
        print self.outscript.output(p)

        p = self.parser.parse(
        '''integer i1; integer i2; integer i3; integer i4; integer i5;
        string a1; string a2; string a3; string a4; string a5;
        string b1; string b2; string b3; string b4; string b5;
        string c1; string c2; string c3; string c4; string c5;
        string d1; string d2; string d3; string d4; string d5;
        string e1; string e2; string e3; string e4; string e5;
        string f1; string f2; string f3; string f4; string f5;
        string g1; string g2; string g3; string g4; string g5;
        string h1; string h2; string h3; string h4; string h5;
        string j1; string j2; string j3; string j4; string j5;
        string k1; string k2; string k3; string k4; string k5;
        string l1; string l2; string l3; string l4; string l5;
        string m1; string m2; string m3; string m4; string m5;
        string n1; string n2; string n3; string n4; string n5;
        string o1; string o2; string o3; string o4; string o5;
        string p1; string p2; string p3; string p4; string p5;
        string s1; string s2; string s3; string s4; string s5;
        fn1(){jump x; @x;} fn2(){integer i3; i4=0; s3=""; fn1();
        if (1) state another;}
        default { timer() { state another; } state_exit() {} }
        state another { timer() { state default; } touch(integer num_det) {} }
        ''')
        self.opt.optimize(p, ['optimize','shrinknames'])
        print self.outscript.output(p)

        p = self.parser.parse(
        '''integer i1; integer i2; integer i3; integer i4; integer i5;
        string a1; string a2; string a3; string a4; string a5;
        string b1; string b2; string b3; string b4; string b5;
        string c1; string c2; string c3; string c4; string c5;
        string d1; string d2; string d3; string d4; string d5;
        string e1; string e2; string e3; string e4; string e5;
        string f1; string f2; string f3; string f4; string f5;
        string g1; string g2; string g3; string g4; string g5;
        string h1; string h2; string h3; string h4; string h5;
        string j1; string j2; string j3; string j4; string j5;
        string k1; string k2; string k3; string k4; string k5;
        string l1; string l2; string l3; string l4; string l5;
        string m1; string m2; string m3; string m4; string m5;
        string n1; string n2; string n3; string n4; string n5;
        string o1; string o2; string o3; string o4; string o5;
        string p1; string p2; string p3; string p4; string p5;
        string s1; string s2; string s3; string s4; string s5;'''
        + ''.join('key k'+str(i).zfill(4)+';\n' for i in xrange(3400))
        + '''fn1(){jump x; @x;} fn2(){integer i3; i4=0; s3=""; fn1();
        if (1) state another;}
        default { timer() { state another; } state_exit() {} }
        state another { timer() { state default; } touch(integer num_det) {} }
        ''')
        self.opt.optimize(p, ['optimize','shrinknames'])

        p = self.parser.parse(
        '''integer i1; integer i2;
        f(integer a, integer b, integer c, integer d, integer e){}
        default{timer(){}}
        ''')
        self.opt.optimize(p, ['optimize','shrinknames','dcr','constfold'])
        out = self.outscript.output(p)
        self.assertEqual(out, 'default\n{\n    timer()\n    {\n    }\n}\n')

        p = self.parser.parse('integer j;integer f(){return 1;}'
            'default{timer(){if (f()) jump x;jump x;@x;\n'
            'if (j) jump x; else return;\n'
            '}}',
            ['extendedglobalexpr'])
        self.opt.optimize(p)
        print self.outscript.output(p)

        p = self.parser.parse(
            'rotation v=<1,2,3,4>;rotation w=<v.z,0,0,0>;\n'
            'integer f(integer x){return 1;}\n'
            'float j=5;\n'
            'default{touch(integer n){\n'
            'v.x = 4; w.x;\n'
            'vector u = llGetVel(); llOwnerSay((string)u.y);\n'
            'vector v1=<llSetRegionPos(<1,1,1>),2,3>; float fq=v1.x;\n'
            'rotation v2=<4,2,3,4>; v2.y;j;f(3);f(n);\n'
            'while(1) do return; while(0);\n'
            '}}',
            ['extendedglobalexpr'])
        self.opt.optimize(p,['optimize', 'shrinknames'])
        print self.outscript.output(p)

        p = self.parser.parse(
            'integer i=2;\n'
            'default{state_entry(){\n'
            'integer j=i+1; integer i=4; llSleep(i+j);\n'
            '}}',
            ['extendedglobalexpr'])
        self.opt.optimize(p, ['optimize', 'shrinknames'])
        print self.outscript.output(p)

    def test_regression(self):


        p = self.parser.parse('''
            integer a; float f = 3;
            x() { if (1) { string s = "x"; s = s + (string)a; } }
            default { timer() { x();a=3;llOwnerSay((string)a); list L; L = [f];
            } }
            ''', ['extendedassignment'])
        self.opt.optimize(p)
        out = self.outscript.output(p)
        self.assertEqual(out, 'integer a;\nx()\n{\n    {\n        '
            'string s = "x";\n        s = s + (string)a;\n    }\n}\n'
            'default\n{\n    timer()\n    {\n        x();\n        a = 3;\n'
            '        llOwnerSay((string)a);\n'
            '    }\n}\n'
            )

        p = self.parser.parse(
            '''key k = "blah";
            list L = [k, "xxxx", 1.0];
            float f;
            integer i = 0;
            vector v = <f, 3, 4>;

            default{timer(){f=4;k="";i=0;v=<0,0,0>;L=[];
            llOwnerSay((string)(L+f+i+v+k));}}
            ''', ['extendedassignment'])
        self.opt.optimize(p)
        out = self.outscript.output(p)
        self.assertEqual(out, 'key k = "blah";\nlist L = [k, "xxxx", 1.];\n'
            'float f = 0;\ninteger i;\nvector v = <0, 3, 4>;\n'
            'default\n{\n    timer()\n    {\n'
            '        f = 4;\n        k = "";\n        i = 0;\n'
            '        v = <((float)0), ((float)0), ((float)0)>;\n        L = [];\n'
            '        llOwnerSay((string)(L + f + i + v + k));\n'
            '    }\n}\n'
            )


        p = self.parser.parse('list L;float f=llList2Float(L, 0);'
            'default{timer(){L=[];f=3;llOwnerSay((string)(L+f));}}',
            ['extendedglobalexpr'])
        self.opt.optimize(p)
        out = self.outscript.output(p)
        self.assertEqual(out, 'list L;\nfloat f = 0;\n'
            'default\n{\n    timer()\n    {\n'
            '        L = [];\n        f = 3;\n'
            '        llOwnerSay((string)(L + f));\n'
            '    }\n}\n')

        self.assertRaises(EParseAlreadyDefined, self.parser.parse,
            'default { timer() {} timer() {} }')

        p = self.parser.parse('default{timer(){\n'
            'llSetPrimitiveParams([llLog(3),llLog(3.0),\n'
            'llStringToBase64((key)""),llGetAgentInfo(""),\n'
            'llStringToBase64(""),llGetAgentInfo((key)"")]);\n'
            '}}\n'
        )
        self.opt.optimize(p, ('optimize','constfold'))
        out = self.outscript.output(p)
        self.assertEqual(out, 'default\n'
                              '{\n'
                              '    timer()\n'
                              '    {\n'
                              '        llSetPrimitiveParams(\n'
                              '            [ 1.0986123\n'
                              '            , 1.0986123\n'
                              '            , ""\n'
                              '            , 0\n'
                              '            , ""\n'
                              '            , 0\n'
                              '            ]);\n'
                              '    }\n'
                              '}\n'
                        )

        p = self.parser.parse('default{timer(){\n'
            'integer i = llGetAgentInfo("12345678-9ABC-DEF0-0123-456789ABCDEF");\n'
            '}}\n'
        )
        self.opt.optimize(p, ('optimize','constfold'))
        out = self.outscript.output(p)
        self.assertEqual(out, 'default\n'
                              '{\n'
                              '    timer()\n'
                              '    {\n'
                              '        integer i = llGetAgentInfo("12345678-'
                              '9ABC-DEF0-0123-456789ABCDEF");\n'
                              '    }\n'
                              '}\n'
                        )

        try:
            self.parser.parse('default { timer() { return } }')
            # should raise EParseSyntax, so it should never get here
            self.assertFalse(True)
        except EParseSyntax as e:
            # should err before first closing brace
            self.assertEqual(e.cno, 27)
        except:
            # should raise no other exception
            self.assertFalse(True)

        p = self.parser.parse('default{timer(){jump x;while(1)@x;}}')
        self.opt.optimize(p)
        out = self.outscript.output(p)
        print out
        # FIXME: DCR produces invalid code, thinks the while can be eliminated
        # due to the jump jumping past it. Extremely corner case, but maybe
        # worth a fix.

    def tearDown(self):
        del self.parser
        del self.opt
        del self.outscript


lslopt.lslcommon.DataPath = __file__[:-len(os.path.basename(__file__))]

if __name__ == '__main__':
    unittest.main()
