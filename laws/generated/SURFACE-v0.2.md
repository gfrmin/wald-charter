# SURFACE-v0.2.md - generated sections, current

The page is signed, so its own sections are as of signing. These are what `laws/page_check.py` renders from
the rules and the references today; the next amendment carries them in.

## Refusals, by name

<!-- generated:refusals -->
- **AFTER**: C2.S12
- **DUPLICATE**: V2.0, V2.1, V2.5, V2.6, V2.7, V2.8
- **FLOAT**: V2.6
- **GLOBAL**: V2.10, C2.S11
- **KERNEL_ROW**: V2.5
- **MISSING**: V2.1, V2.3, V2.5, V2.7, V2.8
- **NOT_A_DECLARATION**: V2.1, V2.2, V2.3, V2.5, V2.6, V2.7, V2.11, V2.14
- **PLATE**: C2.S13
- **PRICE**: V2.5
- **PRIOR**: V2.2, V2.3
- **TABLE_SHAPE**: V2.2, V2.3, V2.4
- **TABLE_SOURCE**: V2.6
- **UNDECLARED_READ**: V2.5, V0.reads
- **UNKNOWN_NAME**: V2.1, V2.5
- **UNSCORED**: C2.S14
<!-- /generated -->

## Traceability

<!-- generated:trace -->
| rule | refused by | poisons | exercised by |
| --- | --- | --- | --- |
| V2.0 | DUPLICATE | 1 | — |
| V2.1 | DUPLICATE, MISSING, NOT_A_DECLARATION, UNKNOWN_NAME | 5 | appendix_a, monitor_all_global |
| V2.2 | NOT_A_DECLARATION, PRIOR, TABLE_SHAPE | 3 | appendix_a, router_credence_prior |
| V2.3 | MISSING, NOT_A_DECLARATION, PRIOR, TABLE_SHAPE | 6 | appendix_a, global_value_unnamed |
| V2.4 | TABLE_SHAPE | 2 | appendix_a, global_value_unnamed, monitor_all_global, router_credence_prior, think_with_globals, two_instruments |
| V2.5 | DUPLICATE, KERNEL_ROW, MISSING, NOT_A_DECLARATION, PRICE, UNDECLARED_READ, UNKNOWN_NAME | 8 | appendix_a, ending_outcome_graded |
| V2.6 | DUPLICATE, FLOAT, NOT_A_DECLARATION, TABLE_SOURCE | 9 | appendix_a_shipped, monitor_shipping, product_kernel_name_counts |
| V2.7 | DUPLICATE, MISSING, NOT_A_DECLARATION | 3 | falsified_refit, falsifiers_before_counts, prefix_falsifier, prefix_falsifier_ending, refit_scored_falsifier |
| V2.8 | DUPLICATE, MISSING | 3 | appendix_a_shipped, monitor_shipping, prefix_falsifier_ending, refit_scored_falsifier |
| V2.9 | — | 0 | after_without_globals, bottom_without_globals |
| V2.10 | GLOBAL | 1 | — |
| V2.11 | NOT_A_DECLARATION | 6 | — |
| V2.12 | — | 0 | appendix_a, appendix_a_shipped |
| V2.13 | — | 0 | appendix_a_shipped, prefix_falsifier_ending, quotes_escaped_digest, quotes_in_names, encoding_check.py |
| V2.14 | NOT_A_DECLARATION | 1 | bottom_without_globals, product_kernel_name_counts |
| C2.S11 | GLOBAL | 2 | — |
| C2.S12 | AFTER | 3 | — |
| C2.S13 | PLATE | 10 | — |
| C2.S14 | UNSCORED | 4 | — |
| V0.reads | UNDECLARED_READ | 1 | — |
<!-- /generated -->
