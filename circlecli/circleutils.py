# -*- coding: utf-8 -*-
"""Utils for CircleCI."""
import os.path as op
import yaml


class InvalidNameError(Exception):
    def __init__(self, message, *args, **kwargs):
        super(InvalidNameError, self).__init__(message, *args, **kwargs)


class UnrecognizedSectionError(Exception):
    def __init__(self, message, *args, **kwargs):
        super(UnrecognizedSectionError, self).__init__(message, *args, **kwargs)


class InvalidSectionError(Exception):
    def __init__(self, message, *args, **kwargs):
        super(InvalidSectionError, self).__init__(message, *args, **kwargs)


def _errant_items(items, allowed_items):
    """Determine if any items are not allowed.

    Args:
        items (list): items to evaluate
        allowed_items (list): the only allowed items

    Returns:
        (set) unique errant values in `items`
    """
    if not isinstance(allowed_items, set):
        allowed_items = set(allowed_items)
    if not isinstance(items, set):
        items = set(items)

    return items.difference(allowed_items)


def validate_circle_yml(filepath):
    """Ensure a circle.yml file is valid according to CircleCI docs.

    Args:
        filepath (str): path to the circle.yml file

    Returns:
        (bool) True if a valid circle.yml
    """
    # obviously the file must be named 'circle.yml'
    if op.basename(filepath) != 'circle.yml':
        raise InvalidNameError(u"Filename must be 'circle.yml'")

    allowed_sections = {'checkout', 'database', 'dependencies', 'deployment',
                        'experimental', 'general', 'machine', 'notify', 'test'}
    fd = open(filepath, 'r')  # let it raise an IOError if no file exists
    circle_yml = yaml.load(fd)  # will throw a ScannerError if not valid YaML
    fd.close()
    circle_sections = circle_yml.keys()

    # check for valid sections
    unrecognized_sections = _errant_items(circle_sections, allowed_sections)
    if len(unrecognized_sections) > 0:
        # we have an unrecognized section
        raise UnrecognizedSectionError(u"The following sections are unrecognized: {}".format(", ".join(unrecognized_sections)))

    # check each section
    for section in circle_sections:
        if section == 'machine':
            conditions = {'pre', 'post'}  # override not allowed
            languages = {'ghc', 'java', 'node', 'php', 'python', 'ruby', 'xcode'}
            system = {'environment', 'hosts', 'services', 'timezone'}
            allowed = conditions.union(languages).union(system)
            try:
                subsections = circle_yml[section].keys()
            except AttributeError:
                raise InvalidSectionError(u"Invalid subsection format in '{}'".format(section))

            # check for valid subsections
            invalid_sections = _errant_items(subsections, allowed)
            if len(invalid_sections) > 0:
                # we have an invalid section
                raise UnrecognizedSectionError(u"Subsections not allowed in '{}': {}".format(section, ", ".join(invalid_sections)))

            # check each subsection
            for subsection in subsections:
                item = circle_yml[section][subsection]
                if subsection in ('environment', 'hosts'):  # dict requirement
                    if not isinstance(item, dict):
                        raise InvalidSectionError(u"Invalid subitem format in '{}.{}'".format(section, subsection))
                elif subsection == 'timezone':  # string requirement
                    if not isinstance(item, basestring):
                        raise InvalidSectionError(u"'{}.{}' subsection must be a single string".format(subsection))
                elif subsection == 'services':  # list requirement
                    if not isinstance(item, list):
                        raise InvalidSectionError(u"'{}.{}' subsection must be a list".format(subsection))
                elif subsection in languages:
                    if not isinstance(item, dict) or len(item.keys()) != 1 or not item.get('version'):
                        raise InvalidSectionError(u"'{}.{}' subsection only supports 'version'".format(section, subsection))
        elif section == 'checkout':
            allowed = {'post'}
            try:
                subsections = circle_yml[section].keys()
            except AttributeError:
                raise InvalidSectionError(u"Invalid subsection format in '{}'".format(section))

            # check for valid subsections
            invalid_sections = _errant_items(subsections, allowed)
            if len(invalid_sections) > 0:
                # we have an invalid section
                raise UnrecognizedSectionError(u"Subsections not allowed in '{}': {}".format(section, ", ".join(invalid_sections)))

            # check the only subsection
            item = circle_yml[section]['post']
            if not isinstance(item, list):
                raise InvalidSectionError(u"'{}' section must be a list".format('post'))
        elif section == 'dependencies':
            conditions = {'pre', 'override', 'post'}
            misc = {'bundler', 'cache_directories'}
            allowed = conditions.union(misc)
            try:
                subsections = circle_yml[section].keys()
            except AttributeError:
                raise InvalidSectionError(u"Invalid subsection format in '{}'".format(section))

            # check for valid subsections
            invalid_sections = _errant_items(subsections, allowed)
            if len(invalid_sections) > 0:
                # we have an invalid section
                raise UnrecognizedSectionError(u"Subsections not allowed in '{}': {}".format(section, ", ".join(invalid_sections)))

            # check each subsection
            for subsection in subsections:
                item = circle_yml[section][subsection]
                if subsection in conditions or subsection == 'cache_directories':
                    if not isinstance(item, list):
                        raise InvalidSectionError(u"'{}' section must be a list".format(subsection))
                else:
                    if not isinstance(item, dict):
                        raise InvalidSectionError(u"'{}.{}' subsection only supports 'without'".format(section, subsection))
                    allowed_subitems = {'without'}
                    subitems = circle_yml[section][subsection].keys()

                    # check for valid subitems
                    invalid_subitems = _errant_items(subitems, allowed_subitems)
                    if len(invalid_subitems) > 0:
                        # we have an invalid section
                        raise UnrecognizedSectionError(u"Subitems not allowed in '{}.{}': {}".format(section, subsection, ", ".join(invalid_subitems)))

                    subsubitem = circle_yml[section][subsection]['without']
                    if not isinstance(subsubitem, list):
                        raise InvalidSectionError(u"'{}.{}.{}' subitem must be a list".format(section, subsection, 'without'))
        elif section == 'database':
            allowed = {'pre', 'override', 'post'}
            try:
                subsections = circle_yml[section].keys()
            except AttributeError:
                raise InvalidSectionError(u"Invalid subsection format in '{}'".format(section))

            # check for valid subsections
            invalid_sections = _errant_items(subsections, allowed)
            if len(invalid_sections) > 0:
                # we have an invalid section
                raise UnrecognizedSectionError(u"Subsections not allowed in '{}': {}".format(section, ", ".join(invalid_sections)))

            # check each subsection
            for subsection in subsections:
                item = circle_yml[section][subsection]
                if not isinstance(item, list):
                    raise InvalidSectionError(u"'{}' section must be a list".format(subsection))
        elif section == 'test':
            conditions = {'pre', 'override', 'post'}
            misc = {'minitest_globs'}
            allowed = conditions.union(misc)
            try:
                subsections = circle_yml[section].keys()
            except AttributeError:
                raise InvalidSectionError(u"Invalid subsection format in '{}'".format(section))

            # check for valid subsections
            invalid_sections = _errant_items(subsections, allowed)
            if len(invalid_sections) > 0:
                # we have an invalid section
                raise UnrecognizedSectionError(u"Subsections not allowed in '{}': {}".format(section, ", ".join(invalid_sections)))

            # check each subsection
            for subsection in subsections:
                item = circle_yml[section][subsection]
                if not isinstance(item, list):
                    raise InvalidSectionError(u"'{}' section must be a list".format(subsection))
        elif section == 'deployment':
            # all subsection names are allowed
            try:
                subsections = circle_yml[section].keys()
            except AttributeError:
                raise InvalidSectionError(u"Invalid subsection format in '{}'".format(section))

            # check each subsection
            for subsection in subsections:
                allowed = {'branch', 'commands', 'heroku', 'owner', 'tag'}
                try:
                    subitems = circle_yml[section][subsection].keys()
                except AttributeError:
                    raise InvalidSectionError(u"Invalid subitem format in '{}.{}'".format(section, subsection))

                # check for valid subitems
                invalid_subitems = _errant_items(subitems, allowed)
                if len(invalid_subitems) > 0:
                    # we have an invalid subitem
                    raise UnrecognizedSectionError(u"Subitems not allowed in '{}.{}': {}".format(section, subsection, ", ".join(invalid_subitems)))

                if 'branch' not in subitems:
                    raise InvalidSectionError(u"'branch' missing from '{}.{}'".format(section, subsection))
                branch = circle_yml[section][subsection]['branch']
                if not isinstance(branch, basestring) and not isinstance(branch, list):
                    raise InvalidSectionError(u"'branch' value not a list or string in '{}.{}'".format(section, subsection))
                commands = circle_yml[section][subsection].get('commands')
                if commands and not isinstance(commands, list):
                    raise InvalidSectionError(u"'{}.{}.{}' subitem must be a list".format(section, subsection, 'commands'))
                heroku = circle_yml[section][subsection].get('heroku')
                if heroku and not isinstance(heroku, dict):
                    raise InvalidSectionError(u"Invalid subitem format in '{}.{}.{}'".format(section, subsection, 'heroku'))
                owner = circle_yml[section][subsection].get('owner')
                if owner and not isinstance(owner, basestring):
                    raise InvalidSectionError(u"'{}.{}.{}' subitem must be a string".format(section, subsection, 'owner'))
        elif section == 'notify':
            allowed = {'webhooks'}
            try:
                subsections = circle_yml[section].keys()
            except AttributeError:
                raise InvalidSectionError(u"Invalid subsection format in '{}'".format(section))

            # check for valid subsections
            invalid_sections = _errant_items(subsections, allowed)
            if len(invalid_sections) > 0:
                # we have an invalid section
                raise UnrecognizedSectionError(u"Subsections not allowed in '{}': {}".format(section, ", ".join(invalid_sections)))

            webhooks = circle_yml[section]['webhooks']
            if not isinstance(webhooks, list):
                raise InvalidSectionError(u"'{}.{}' subsection must be a list".format(section, 'webhooks'))
            for url_address in webhooks:
                if not isinstance(url_address, dict) or not url_address.get('url'):
                    raise InvalidSectionError(u"'{}.{}' subsection must be a list of 'url: <url>' items".format(section, 'webhooks'))
        elif section == 'general':
            allowed = {'artifacts', 'branches', 'build_dir'}
            try:
                subsections = circle_yml[section].keys()
            except AttributeError:
                raise InvalidSectionError(u"Invalid subsection format in '{}'".format(section))

            # check for valid subsections
            invalid_sections = _errant_items(subsections, allowed)
            if len(invalid_sections) > 0:
                # we have an invalid section
                raise UnrecognizedSectionError(u"Subsections not allowed in '{}': {}".format(section, ", ".join(invalid_sections)))

            for subsection in subsections:
                if subsection == 'artifacts':
                    item = circle_yml[section][subsection]
                    if not isinstance(item, list):
                        raise InvalidSectionError(u"'{}.{}' subsection must be a list".format(section, subsection))
                elif subsection == 'branches':
                    allowed_subitems = {'ignore', 'only'}
                    try:
                        subitems = circle_yml[section][subsection].keys()
                    except AttributeError:
                        raise InvalidSectionError(u"Invalid subitem format in '{}.{}'".format(section, subsection))

                    # check for valid subitems
                    invalid_subitems = _errant_items(subitems, allowed_subitems)
                    if len(invalid_subitems) > 0:
                        # we have an invalid subitem
                        raise UnrecognizedSectionError(u"Subitems not allowed in '{}.{}': {}".format(section, ", ".join(invalid_sections)))

                    for subitem in subitems:
                        item = circle_yml[section][subsection][subitem]
                        if not isinstance(item, list):
                            raise InvalidSectionError(u"'{}.{}.{}' subitem must be a list".format(section, subsection, subitem))
                elif subsection == 'build_dir':
                    item = circle_yml[section][subsection]
                    if not isinstance(item, basestring):
                        raise InvalidSectionError(u"'{}.{}' subsection must be a string".format(section, subsection))
        elif section == 'experimental':
            allowed = {'notify'}  # currently only notify
            try:
                subsections = circle_yml[section].keys()
            except AttributeError:
                raise InvalidSectionError(u"Invalid subsection format in '{}'".format(section))

            # check for valid subsections
            invalid_sections = _errant_items(subsections, allowed)
            if len(invalid_sections) > 0:
                # we have an invalid section
                raise UnrecognizedSectionError(u"Subsections not allowed in '{}': {}".format(section, ", ".join(invalid_sections)))

            allowed_subitems = {'branches'}
            try:
                subitems = circle_yml[section]['notify'].keys()
            except AttributeError:
                raise InvalidSectionError(u"Invalid subitem format in '{}.{}'".format(section, 'notify'))

            # check for valid subitems
            invalid_subitems = _errant_items(subitems, allowed_subitems)
            if len(invalid_subitems) > 0:
                # we have an invalid section
                raise UnrecognizedSectionError(u"Subitems not allowed in '{}.{}': {}".format(section, 'notify', ", ".join(invalid_subitems)))

            for subitem in subitems:
                allowed_subsubitems = {'ignore', 'only'}
                try:
                    subsubitems = circle_yml[section]['notify'][subitem].keys()
                except AttributeError:
                    raise InvalidSectionError(u"Invalid subitem format in '{}.{}.{}'".format(section, 'notify', subitem))

                # check for valid subsubitems
                invalid_subsubitems = _errant_items(subsubitems, allowed_subsubitems)
                if len(invalid_subsubitems) > 0:
                    # we have an invalid subsubitem
                    raise UnrecognizedSectionError(u"Subitems not allowed in '{}.{}.{}': {}".format(section, 'notify', subitem, ", ".join(invalid_subsubitems)))

                for subsubitem in subsubitems:
                    item = circle_yml[section]['notify'][subitem][subsubitem]
                    if not isinstance(item, list):
                        raise InvalidSectionError(u"'{}.{}.{}.{}' subitem must be a list".format(section, 'notify', subitem, subsubitem))
    return True