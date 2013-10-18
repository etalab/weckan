WeCKAN
======

Etalab front-end to CKAN.

Installation
------------

Weckan require a development version of webassets.

An up to date version is hosted at `noirbizarre/webassets#for-weckan`_ while the following pull-request are pending:

- `#260`_
- `#266`_

To install you need to build the package before (until its released on PyPI)

.. code-block:: console

    $ git clone https://github.com/etalab/weckan.git
    $ cd weckan
    $ make dist
    $ pip install git+https://github.com/noirbizarre/webassets.git@for-weckan#egg=webassets
    $ pip install dist/Weckan*.tar.gz
    $ pip install ckan==2.1
    $ pip install -r https://raw.github.com/okfn/ckan/ckan-2.1/requirements.txt


Development
-----------

Weckan use bower to collect static assets and webassets to build them.

Before starting to develop you need to run:

.. code-block:: console

    $ bower install
    $ make assets


.. _noirbizarre/webassets#for-weckan: https://github.com/noirbizarre/webassets/tree/for-weckan
.. _#260: https://github.com/miracle2k/webassets/pull/260
.. _#266: https://github.com/miracle2k/webassets/pull/266
