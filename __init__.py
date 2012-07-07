
# code TODO:
# * db-driven select
# * fields.py with fields that mark themselfs as save

"""
# concise overview of WTForms architecture: forms, fields, widgets, validators
# * `class:Form`s: core container of WTForms, represents collection of Fields.
# * Fields: convert from HTML <form/> data representation to Python and wise-versa.
# * Widgets: renders fields HTML.
# * Validators: specify validation rules for Fields.
# .. see:: http://wtforms.simplecodes.com/docs/1.0.1/crash_course.html

# cons:
# * better syntax (TODO: side to side demonstration of ContentUnitsSearch form)



# * simple extensibility (TODO: example with form inheritance)
# * simple and extensible class based fields and widgets (TODO: example with
#   that huge widget with lots of checkboxes from user or network setup)
#
# * integrates well with sqlalchemy, web2py's DAL and Django ORM
#   (really it can be easily integrated with anything: DAL integration was
#       written by me in one evening, and it takes only TODO NNN lines of code
#       TODO [link to github])
# * likewise, can be used with any templating language
# * integrates well with other web frameworks: flask-wtforms, TODO
#
# * well tested (and web2py's forms ARE NOT TESTED AT ALL, TODO: as far as I can tell)
#       TODO: calc test coverage
#               n%, which is pretty well coverage
# * well documented (overview as well as detailed reference documentation;
#   docstrings TODO)
# * TODO: good comunity
#       google trends, mailing lists, commiters
# * TODO: model-form pattern, `.save()`, OOP-style::
#           it is possible to incapsulate specific logic in the form itself
#
#   class ContentUnitsSearch(Form):
#       ...
#       def getFoundCountentUnits(self):
#           return ContentUnits(db).getSearchResult(**self.data)
#
#   def contentUnitsSearchView():
#       form = ContentUnitsSearch(request.post_vars):
#       contentUnits = None
#       if form.validate():
#           contentUnits = form.getFoundCountentUnits()
#       return {
#           "form": form,
#           "contentUnits": contentUnits,
#       }
#       # btw, in that particular case of cu searching it will be better to
#       # return that context as json
#
#   def createContentUnitView():
#       form = ContentUnitForm(request.post_vars)
#       if form.validate():
#           newShinyContentUnit = form.save()
#           redirect("somewhere")
#       return {"form": form}
#
# * last but not least: good code (TODO: link to web2py's code VS link to wtforms code; or side to
#   side demonstration)
"""


# thanks for watching. btw, as i've pretty failed with demonstrating sqlalchemy
# cons-es, to fix that i can prepare similar discriptive presentation about it.
# if it can help to make decision on that

# TODO: look at the other form libraries
