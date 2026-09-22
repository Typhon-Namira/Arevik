# Local model policy

Arevik prefers self-hosted models that can legally support a commercial product.

Before adding a model to production, record:

- exact model/repository ID,
- model version or commit,
- license,
- supported languages,
- CPU/RAM requirements,
- measured latency on the target AWS instance,
- measured quality on an Arevik-owned English/Armenian evaluation set.

Do not assume that a model is acceptable because it is downloadable for free.

The Phase 1 code keeps each model behind an adapter specifically so a model can be replaced after quality, latency, or licensing review.
