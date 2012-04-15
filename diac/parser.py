from pyparsing import Word, Optional, OneOrMore, Group, Regex, Literal, \
        Forward, ZeroOrMore, operatorPrecedence, opAssoc, Combine, oneOf,\
        indentedBlock
from pyparsing import alphas, alphanums, nums, quotedString, lineEnd, lineStart

import collections


indentStack = [1]


class Tree(collections.Iterable):
    def __iter__(self):
        return iter(self.tokens)

    def replace_tokens(self, tokens):
        self.tokens = tokens

    def __repr__(self):
        return repr(self.__class__) + '(' + repr(self.tokens) + ')'


class Dialog(Tree):
    def __init__(self, tokens):
        self.tokens = tokens[1:]
        definition = tokens[0]

        try:
            self.name, self.extends = definition
        except ValueError:
            self.name, = definition


class Response(Tree):
    def __init__(self, tokens):
        self.text = tokens[0]
        self.tokens = tokens[1:]


class Option(Tree):
    def __init__(self, tokens):
        self.text = tokens[1]
        self.tokens = tokens[2:]


class Variable(object):
    def __init__(self, tokens):
        self.object_name = tokens[0][0]
        self.variable = tokens[0][2]


class Expression(Tree):
    def __init__(self, tokens):
        self.tokens = tokens


class IfStatement(Tree):
    def __init__(self, tokens):
        self.tokens = tokens[1:]


class Event(object):
    def __init__(self, tokens):
        self.target = tokens[1]
        self.message = tokens[2]

    def __unicode__(self):
        return u'{0}!{1}'.format(self.target, self.message)


def convertIntegers(tokens):
    return int(tokens[0])


def convertFloats(tokens):
    return float(tokens[0])


text = Regex(r'[^\n]+')
atom = Word(alphas, alphanums + '_')
var_separator = Literal(':')
integer = Word(nums).setParseAction(convertIntegers)
real = Combine(Optional(oneOf("+ -")) + Word(nums) + "." + \
               Optional(Word(nums)) + \
               Optional(oneOf("e E") + Optional(oneOf("+ -")) + Word(nums)))\
               .setName("real")\
               .setParseAction(convertFloats)

var = Group(atom + var_separator + atom).setParseAction(Variable)

term = real | integer | var
comparison_term = atom | quotedString

plus = Literal('+')
minus = Literal('-')
multiply = Literal('*')
divide = Literal('/')
signop = minus

lpar = Literal('(').suppress()
rpar = Literal(')').suppress()

mulop = multiply | divide
addop = plus | minus

expression = operatorPrecedence(term,
        [(signop, 1, opAssoc.RIGHT),
         (mulop, 2, opAssoc.LEFT),
         (addop, 2, opAssoc.LEFT)]).setParseAction(Expression)

comparable_expression = expression | comparison_term

less_than = Literal('<')
greater_than = Literal('>')
less_than_or_equal = Literal('<=')
greater_than_or_equal = Literal('>=')
equals = Literal('=')
not_equals = Literal('!=')
comparison = less_than | less_than_or_equal | greater_than | \
             greater_than_or_equal | equals | not_equals

and_logic = Literal('and')
or_logic = Literal('or')
binary_logic = and_logic | or_logic
not_logic = Literal('not')

conditionals = Forward()

conditional = Group(comparable_expression + comparison + comparable_expression) | \
              Group(lpar + conditionals + rpar)
              
conditionals << Optional(not_logic) + conditional + ZeroOrMore(binary_logic + conditional)

if_keyword = Literal('if')

if_statement = (if_keyword + conditionals).setParseAction(IfStatement)

option = Forward()

response_definition = text + lineEnd.suppress() + Optional(if_statement + Literal('then').suppress())
response = (response_definition + ZeroOrMore(indentedBlock(option, indentStack, True))).setParseAction(Response)

event_send = Literal('->')
event_message_separator = Literal('!').suppress()

event_atom = atom.copy().setParseAction(lambda t: repr(t[0]))
event_message = quotedString | event_atom
event_send_separator = Literal(',').suppress()
event_statement = (event_send + event_atom + event_message_separator + event_message).setParseAction(Event)

options_delimiter =  Literal('~')
options_definition = options_delimiter + text + Optional(event_statement + ZeroOrMore(event_send_separator + event_statement))

option << (options_definition + ZeroOrMore(indentedBlock(response, indentStack, True))).setParseAction(Option)

dialog_begin = Literal('begin').suppress() + Group(atom + Optional(Literal('extends').suppress() + atom))
dialog_end = Literal('end').suppress()
dialog = (dialog_begin + ZeroOrMore(indentedBlock(response, indentStack, True)) + dialog_end).setParseAction(Dialog)

dialogs = ZeroOrMore(indentedBlock(dialog, indentStack, False))


if __name__ == '__main__':
    print expression.parseString("1 * 2.5 * 8 * (9 + 3.12 - 1 + 4) / |(2 - -(7 - 9))")

    print dialogs.parseString("""begin testDialog
  Hello, this is a greating response!
    if player:health > 10 then
    ~ This is option A
    ~ This is option B with a response
      Option B Response
          ~ Yes
          ~ No, send event
            -> player!test,
            -> self!test2
  Another possible initial response.
    ~ Alt Option 1
    ~ Alt Option 2
end
begin testDialog2 extends testDialog
end
""")
