Outlines should be extensible. Each system should be able to put in relevant
data (e.g. scheduling, pre-requisites, etc.)

Each CourseOutline

Q: Why not use Block Transformers?

A: Block Transformers and the Course Blocks API are designed to allow powerful
querying at any level of granularity across XBlock content for the course as a
whole. But to support this level of power and flexibility (e.g. DAGs, arbitrary
depth, any field data, etc.), it's fairly complex and tends to have a lot of
up-front costs with how data is stored. This interface is intended to be much
more limited, but also hopefully much simpler and easier to make performant.


Extension points:
* Hide from user entirely.
* Show item but disable navigation (not currently accessible, e.g. pre-reqs)
* Add supplemental data.

Doesn't look like we need to worry about cohorts? Usually at unit level?

* Hiding (and showing?) groups of sequences, applied in order. (e.g. beta
  users?) --> Omitted entirely if you're course staff.
* Supplementary data
