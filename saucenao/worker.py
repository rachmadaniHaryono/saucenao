#!/usr/bin/python
# -*- coding: utf-8 -*-
import time

try:
    from titlesearch import get_similar_titles
except ImportError:
    get_similar_titles = None

from saucenao import SauceNao, FileHandler


class Worker(SauceNao):
    """
    Worker class for checking a list of files
    """

    def __init__(self, files, *args, **kwargs):
        """
        initializing function

        :type files: list|tuple|Generator
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.complete_file_list = files

    def run(self):
        """Check all files with SauceNao and execute the specified tasks

        :return:
        """
        for file_name in self.files:
            start_time = time.time()

            filtered_results = self.check_file(file_name)

            if not filtered_results:
                self.logger.info('No results found for image: {0:s}'.format(file_name))
                continue

            if self._move_to_categories:
                self.move_to_categories(file_name=file_name, results=filtered_results)
            else:
                yield {
                    'filename': file_name,
                    'results': filtered_results
                }

            duration = time.time() - start_time
            if duration < (30 / SauceNao.LIMIT_30_SECONDS):
                self.logger.debug("sleeping '{:.2f}' seconds".format((30 / SauceNao.LIMIT_30_SECONDS) - duration))
                time.sleep((30 / SauceNao.LIMIT_30_SECONDS) - duration)

    @property
    def excludes(self):
        """Property for excludes

        :return:
        """
        if self._exclude_categories:
            return [l.lower() for l in self._exclude_categories.split(",")]
        else:
            return []

    @property
    def files(self):
        """Property for files

        :return:
        """
        if self._start_file:
            # change files from generator to list
            files = list(self.complete_file_list)
            try:
                return files[files.index(self._start_file):]
            except ValueError:
                return self.complete_file_list
        return self.complete_file_list

    def move_to_categories(self, file_name: str, results):
        """Check the file for categories and move it to the corresponding folder

        :type file_name: str
        :type results: list|tuple|Generator
        :return: bool
        """
        categories = self.get_content_value(results, SauceNao.CONTENT_CATEGORY_KEY)

        if not categories:
            self.logger.info("no categories found for file: {0:s}".format(file_name))
            return False

        self.logger.debug('categories: {0:s}'.format(', '.join(categories)))

        # since many pictures are tagged as original and with a proper category
        # we remove the original category if we have more than 1 category
        if len(categories) > 1 and 'original' in categories:
            categories.remove('original')

        # take the first category
        category = categories[0]

        category = self.get_similar_title(category)

        # sub categories we don't want to move like original etc
        if category.lower() in self.excludes:
            self.logger.info("skipping excluded category: {0:s} ({1:s})".format(category, file_name))
            return False

        self.logger.info("moving {0:s} to category: {1:s}".format(file_name, category))
        FileHandler.move_to_category(file_name, category, base_directory=self._directory)
        return True

    def get_similar_title(self, category):
        """

        :param category:
        :return:
        """
        if get_similar_titles:
            similar_titles = get_similar_titles(category)

            if similar_titles and similar_titles[0]['similarity'] * 100 >= self._title_minimum_similarity:
                self.logger.info(
                    "Similar title found: {0:s}, {1:s} ({2:.2f}%)".format(
                        category, similar_titles[0]['title'], similar_titles[0]['similarity'] * 100))
                return similar_titles[0]['title']

        return category
