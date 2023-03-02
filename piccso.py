##########
# IMPORTS
##########

from string_with_arrows import *

##########
# CONSTANTS
##########

DIGITS = '0123456789'

##########
# ERRORS
##########

class Error:
    def __init__(self, pos_start, pos_end, error_name, details):
        self.pos_start = pos_start
        self.pos_end = pos_end    
        self.error_name = error_name
        self.details = details

    def as_string(self):
        result = f"{self.error_name}: {self.details}"
        result += f"File {self.pos_start.fn}, line {self.pos_start.ln + 1}"
        result += "\n\n" + string_with_arrows(self.pos_start.ftxt, self.pos_start, self.pos_end)
        return result
    
class IllegalCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Illegal Character\n', details)

class InvalidSyntaxError(Error):
    def __init__(self, pos_start, pos_end, details=''):
        super().__init__(pos_start, pos_end, 'Invalid Syntax\n', details)

##########
# POSITION
##########

class Position:
    def __init__(self, index, ln, col, fn, ftxt):
        self.index = index
        self.ln = ln
        self.col = col
        self.fn = fn
        self.ftxt = ftxt
    
    def advance(self, cur_char=None):
        self.index += 1
        self.col += 1

        if cur_char == '\n':
            self.ln += 1
            self.col = 0

        return self
    
    def copy(self):
        return Position(self.index, self.ln, self.col, self.fn, self.ftxt)
    
##########
# TOKENS
##########

TT_INT    = "INT"
TT_FLOAT  = "FLOAT"
TT_PLUS   = "PLUS"
TT_MINUS  = "MINUS"
TT_MUL    = "MUL"
TT_DIV    = "DIV"
TT_LPAREN = "LPAREN"
TT_RPAREN = "RPAREN"
TT_EOF    = "EOF"


class Token:
    def __init__(self, type_, value=None, pos_start=None, pos_end=None):
        self.type = type_
        self.value = value

        if pos_start:
            self.pos_start = pos_start.copy()
            self.pos_end = pos_start.copy()
            self.pos_end.advance()
        if pos_end:
            self.pos_end = pos_end

    def __repr__(self):
        if self.value:
            return f"{self.type}:{self.value}"
        else:
            return f"{self.type}"
        
##########       
# LEXER
##########

class Lexer:
    def __init__(self, fn, text):
        self.fn = fn
        self.text = text
        self.pos = Position(-1, 0, -1, fn, text)
        self.cur_char = None
        self.advance()

    def advance(self):
        self.pos.advance(self.cur_char)
        self.cur_char = self.text[self.pos.index] if self.pos.index < len(self.text) else None

    def make_tokens(self):
        tokens = []

        while self.cur_char != None:
            if self.cur_char in " \t":
                self.advance()
            elif self.cur_char in DIGITS:
                tokens.append(self.make_number())
                # don't advance as it advances inside of the function make_number(), this is so that we can get numbers that are not just 1 position long
            elif self.cur_char == '+':
                tokens.append(Token(TT_PLUS, pos_start=self.pos))
                self.advance()
            elif self.cur_char == '-':
                tokens.append(Token(TT_MINUS, pos_start=self.pos))
                self.advance()
            elif self.cur_char == '*':
                tokens.append(Token(TT_MUL, pos_start=self.pos))
                self.advance()
            elif self.cur_char == '/':
                tokens.append(Token(TT_DIV, pos_start=self.pos))
                self.advance()
            elif self.cur_char == '(':
                tokens.append(Token(TT_LPAREN, pos_start=self.pos))
                self.advance()
            elif self.cur_char == ')':
                tokens.append(Token(TT_RPAREN, pos_start=self.pos))
                self.advance()
            else:
                pos_start = self.pos.copy()
                char = self.cur_char
                self.advance()
                return [], IllegalCharError(pos_start, self.pos, f"'{char}'")

        tokens.append(Token(TT_EOF, pos_start=self.pos)) 
        return tokens, None
    
    def make_number(self):
        num_str = ''
        dot_count = 0
        pos_start = self.pos.copy()

        while self.cur_char != None and self.cur_char in DIGITS+'.':
            if self.cur_char == '.':
                if dot_count == 1:
                    break # more than 1 dot
                dot_count += 1
                num_str += '.'
            else:
                num_str += self.cur_char
            self.advance()

        if dot_count == 0:
            return Token(TT_INT, int(num_str), pos_start, self.pos) # self.pos is basically just pos_end
        else:
            return Token(TT_FLOAT, float(num_str), pos_start, self.pos) # self.pos is basically just pos_end
        
##########
# NODES
##########

class NumberNode:
    def __init__(self, tok):
        self.tok = tok
    
    def __repr__(self):
        return f"{self.tok}"

class BinOpNode:
    def __init__(self, left_node, op_tok, right_node):
        self.left_node = left_node
        self.op_tok = op_tok
        self.right_node = right_node
    
    def __repr__(self):
        return f"({self.left_node}, {self.op_tok}, {self.right_node})"
    
class UnaryOpNode:
    def __init__(self, op_tok, node):
        self.op_tok = op_tok
        self.node = node
    
    def __repr__(self):
        return f"({self.op_tok}, {self.node})"
    
##########
# PARSE RESULT
##########
    
class ParseResult:
    def __init__(self):
        self.error = None
        self.node = None

    def register(self, result):
        if isinstance(result, ParseResult):
            if result.error:
                self.error = result.error
            return result.node
        return result

    def success(self, node):
        self.node = node
        return self

    def failure(self, error):
        self.error = error
        return self

##########
# PARSER
##########

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.tok_index = -1
        self.advance()

    def advance(self):
        self.tok_index += 1
        if self.tok_index < len(self.tokens):
            self.cur_tok = self.tokens[self.tok_index]
        return self.cur_tok
    
    def parse(self):
        response = self.expr()
        if not response.error and self.cur_tok.type != TT_EOF:
            return response.failure(InvalidSyntaxError(self.cur_tok.pos_start, self.cur_tok.pos_end, "Expected Operand '+' | '-' | '*' | '/'"))
        return response

    ##########

    def factor(self):
        response = ParseResult()
        tok = self.cur_tok

        if tok.type in (TT_PLUS, TT_MINUS):
            response.register(self.advance())
            factor = response.register(self.factor())
            if response.error:
                return response
            return response.success(UnaryOpNode(tok, factor))

        elif tok.type in (TT_INT, TT_FLOAT):
            response.register(self.advance())
            return response.success(NumberNode(tok))
            
        
        elif tok.type == TT_LPAREN:
            response.register(self.advance())
            expr = response.register(self.expr())
            if response.error:
                return response
            if self.cur_tok.type == TT_RPAREN:
                response.register(self.advance())
                return response.success(expr)
            else:
                return response.failure(InvalidSyntaxError(self.cur_tok.pos_start, self.cur_tok.pos_end, "Expected ')'"))

        return response.failure(InvalidSyntaxError(tok.pos_start, tok.pos_end, "Expected type INT|FLOAT"))

    def term(self):
        return self.bin_op(self.factor, (TT_MUL, TT_DIV))

    def expr(self):
        return self.bin_op(self.term, (TT_MINUS, TT_PLUS))
    
    #######

    def bin_op(self, func, ops):
        response = ParseResult()
        left = response.register(func())

        if response.error:
            return response

        while self.cur_tok.type in ops:
            op_tok = self.cur_tok
            response.register(self.advance())
            right = response.register(func())
            if response.error:
                return response
            left = BinOpNode(left, op_tok, right)

        return response.success(left) # left factorNode is now a BinOpNode


##########
# RUN
##########

def run(fn, text):
    # generate tokens
    lexer = Lexer(fn, text)
    tokens, error =  lexer.make_tokens()
    if error:
        return None, error

    # generate abstract syntax tree
    parser = Parser(tokens)
    ast = parser.parse()

    return ast.node, ast.error