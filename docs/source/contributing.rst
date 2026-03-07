.. title:: Contributing
.. meta::
   :description: How to contribute to SMACC2 -- reporting bugs, submitting pull requests, writing documentation, and coding standards.

Contributing
============

Thank you for your interest in contributing to SMACC2. Whether it is a bug report, new feature, correction, or additional documentation, we greatly value feedback and contributions from our community.

- **Repository:** `robosoft-ai/SMACC2 <https://github.com/robosoft-ai/SMACC2>`_
- **License:** `Apache 2.0 <http://www.apache.org/licenses/LICENSE-2.0.html>`_
- **ROS 2 distro:** Jazzy (Ubuntu 24.04)

|

Reporting Bugs and Feature Requests
------------------------------------

We welcome you to use the GitHub issue tracker to report bugs or suggest features.

Before filing an issue, please check `existing open issues <https://github.com/robosoft-ai/SMACC2/issues>`_ or `recently closed issues <https://github.com/robosoft-ai/SMACC2/issues?q=is%3Aissue+is%3Aclosed>`_ to make sure somebody else has not already reported it.

When filing an issue, please include as much information as you can:

- A reproducible test case or series of steps
- The version of SMACC2 and ROS 2 being used
- Any modifications you have made relevant to the bug
- Anything unusual about your environment or deployment

|

Contributing via Pull Requests
-------------------------------

Contributions via pull requests are much appreciated. Before sending us a pull request, please ensure that:

1. **Limited scope.** Your PR should do one thing or one set of things. Avoid adding unrelated fixes to PRs. Put those on separate PRs.
2. **Descriptive title.** Give your PR a descriptive title. Add a short summary if required.
3. **Green pipeline.** Make sure the CI pipeline passes.
4. **Request reviews.** Do not be afraid to request reviews from maintainers.
5. **New code = new tests.** If you are adding new functionality, add tests exercising the code and serving as live documentation of your original intention.

**Submitting a Pull Request**

1. Fork the `repository <https://github.com/robosoft-ai/SMACC2>`_.
2. Modify the source. Focus on the specific change you are contributing -- if you also reformat all the code, it will be hard to review your change.
3. Ensure local tests pass:

   .. code-block:: bash

      colcon test
      pre-commit run -a   # requires: sudo apt install pre-commit

4. Commit to your fork using clear commit messages.
5. Send a pull request, answering any default questions in the pull request interface.
6. Pay attention to any automated CI failures reported in the pull request, and stay involved in the conversation.

GitHub provides additional documentation on `forking a repository <https://help.github.com/articles/fork-a-repo/>`_ and `creating a pull request <https://help.github.com/articles/creating-a-pull-request/>`_.

|

Finding Contributions to Work On
----------------------------------

Looking at the existing issues is a great way to find something to contribute. The `"help wanted" <https://github.com/robosoft-ai/SMACC2/issues?q=is%3Aopen+is%3Aissue+label%3A%22help+wanted%22>`_ label is a great place to start.

|

Contributing to Documentation
-------------------------------

This documentation site lives in a separate repository:

- **Docs repository:** `robosoft-ai/smacc2_docs <https://github.com/robosoft-ai/smacc2_docs>`_

**Building Locally**

.. code-block:: bash

   cd ~/ros2_ws/src
   git clone https://github.com/robosoft-ai/smacc2_docs.git
   cd smacc2_docs
   pip install -r docs/requirements.txt
   sphinx-build -b html docs/source docs/build/html

Then open ``docs/build/html/index.html`` in a browser.

**Writing Guidelines**

- Pages use reStructuredText (``.rst``) format with ``.. title::`` and ``.. meta:: :description:`` directives for SEO.
- Follow the `Diataxis framework <https://diataxis.fr/>`_: tutorials teach, how-to guides solve, concepts explain, reference describes.
- Use a single ``|`` line between top-level sections for consistent spacing.
- Code examples should be drawn from real state machines in the ``smacc2_sm_reference_library`` or real client libraries whenever possible.
- Follow the SMACC2 :doc:`naming convention <concepts/basics>` (``Sm``, ``Ms``, ``St``, ``Or``, ``Cl``, ``Cb``, ``Cp`` prefixes) in all examples.

|

Coding Standards
-----------------

- Follow the existing code style in the repository.
- Use ``pre-commit`` hooks for automatic formatting and linting.
- Header files use ``.hpp`` extension; source files use ``.cpp``.
- Follow the SMACC2 :doc:`naming convention <concepts/basics>` for all classes and files.
- Keep state machines header-only (states defined in ``.hpp`` files).
- Prefer the component-based architecture: clients orchestrate, components implement, behaviors consume.

|

Licensing
----------

Any contribution that you make to this repository will be under the Apache 2.0 License, as dictated by that `license <http://www.apache.org/licenses/LICENSE-2.0.html>`_:

   *"Unless You explicitly state otherwise, any Contribution intentionally submitted for inclusion in the Work by You to the Licensor shall be under the terms and conditions of this License, without any additional terms or conditions."*
