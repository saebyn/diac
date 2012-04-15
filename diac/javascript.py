"""
Target compiler output for Javascript.
"""
import collections
import types
from diac.parser import Expression, Variable, Dialog, Response, Option, Event, IfStatement


def descend_for(*filters):
    def decorate(func):
        def inner(tree):
            if type(tree) is types.InstanceType and tree.__class__ in filters:
                tree = func(tree)
            elif type(tree) in filters:
                tree = func(tree)

            if is_iterable_collection(tree):
                results = [inner(branch) for branch in tree]
                try:
                    tree.replace_tokens(results)
                    return tree
                except (AttributeError, TypeError):
                    return results
            else:
                return tree

        return inner
    return decorate


def is_iterable_collection(el):
    return isinstance(el, collections.Iterable) and not isinstance(el, basestring)


@descend_for(int, float)
def format_numbers(value):
    """
    Convert internal float and int representations into JS.
    """
    return repr(value)

@descend_for(Variable)
def variables(tree):
    return u'context[{0!r}].{1}'.format(tree.object_name, tree.variable)


@descend_for(IfStatement)
def if_statements(tree):
    return [u"""
    this.check = function () {
      return (""", tree.tokens, u""");
    };
"""]

@descend_for(Expression)
def expressions(tree):
    return u''.join(tree.tokens)


@descend_for(Response)
def responses(tree):
    """
    Insert a new response class instance into the current object.

    Response objects have `text` and `options` attributes and a
    `choose` method.
    """
    return [u"""
  this.responses.push(new function () {{
    this.text = {0!r};
    this.options = [];

    this.getOptions = function () {{ return getOptions.apply(this); }};
    this.choose = function (option) {{ return chooseOption.apply(this, context, option); }};

 """.format(tree.text), tree.tokens, u"""
  });
 """]


@descend_for(Event)
def events(event):
    """
    Add an event dispatcher to the current object.
    """
    return [u"""
      this.events.push([{0}, {1}]);
""".format(event.target, event.message)]

@descend_for(Option)
def options(tree):
    """
    Insert a new option class instance into the current object.
    """
    return [u"""
    this.options.push(new function () {{
      this.text = {0!r};
      this.events = [];
      this.responses = [];

      this.getResponse = function () {{ return getResponse.apply(this); }};
""".format(tree.text), tree.tokens, u"""
    });
"""]


@descend_for(Dialog)
def dialogs(dialog):
    """
    Create a dialog class with a single method `getResponse`.

    This `getResponse` method chooses which response to return.
    """
    # TODO support extending dialogs... somehow
    return [u"""
  dialogs[{0!r}] = new function (context) {{
    this.responses = [];

    this.getResponse = function () {{ return getResponse.apply(this); }};

""".format(dialog.name), dialog.tokens, u"""
  };
"""]


iterations = [format_numbers,
              variables,
              expressions,
              if_statements,
              events,
              responses,
              options,
              dialogs]


def flatten(l):
    for el in l:
        if is_iterable_collection(el):
            for sub in flatten(el):
                yield sub
        else:
            yield el


def target(parse_tree):
    """
    Return Javascript as string.
    """
    intermediate = parse_tree
    for iteration in iterations:
        intermediate = iteration(intermediate)

    body = u''.join(flatten(intermediate))

    return u"""
(function () {{
  function getResponse() {{
    var i, response;
    for (i = 0; i < this.responses.length; i++) {{
      response = this.responses[i];
      if ( response.check === undefined || response.check() ) {{
        return response;
      }}
    }}
  
    return false;
  }}
  
  function chooseOption(context, optionText) {{
    var i, j, event, option;
    for (i = 0; i < this.options.length; i++) {{
      option = this.options[i];
      if (option.text === optionText) {{
        for (j = 0; j < option.events.length; j++) {{
          event = option.events[j];
          if (context[event[0]] !== undefined) {{
            context[event[0]].trigger(event[1], context.self);
          }}
        }}
          
        return option;
      }}
    }}
  }}
  
  function getOptions() {{
    var options = [];
    var i;
    for (i = 0; i < this.options.length; i++) {{
      options.push(this.options[i].text);
    }}
  
    return options;
  }}
  
  var dialogs = exports.dialogs = {{}};
  
  {0}
}})();
""".format(body) 
