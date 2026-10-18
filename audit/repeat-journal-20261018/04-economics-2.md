# Sovereign source reader: 04-economics, part 2

Derived reading aid; original file bytes and rights are authoritative. No functions or file sections have been omitted from the listed files. Cite `original/path:line` using the numbered column. Read at the exact review commit supplied in the user message.

## simulation-core/game-forge/sim/params.json

Original bytes: 42824; SHA256: `406fa0db3f52fc2e12e8becdf54a9b0b4620461ab4c501bb1b0c788ec7c8243b`. Original source line numbers follow.

````text
    1 | {
    2 |   "schema": "life-sim-v1",
    3 |   "sources": {
    4 |     "design": "Game calibration, not measured physiology; SPEC_CH1_v0 S1-S4/S12 and DECISIONS O6/P6. Offline reading 2026-10-15.",
    5 |     "lally": "Lally et al. (2010), How are habits formed: Modelling habit formation in the real world, European Journal of Social Psychology 40:998-1009, DOI 10.1002/ejsp.674. User-provided median 66 days, range 18-254; 95% asymptote criterion. Not web-verified here.",
    6 |     "practice": "Newell & Rosenbloom (1981), Mechanisms of skill acquisition and the law of practice, in Cognitive Skills and Their Acquisition. Power-law shape only; exponent/hours are game assumptions.",
    7 |     "burnout": "Maslach, Schaufeli & Leiter (2001), Job Burnout, Annual Review of Psychology 52:397-422. Chronic stress is qualitative motivation; all rates/thresholds are invented game calibration.",
    8 |     "sleep": "Borbely (1982), A two process model of sleep regulation, Human Neurobiology 1:195-204. Qualitative saturation inspiration, not this energy equation.",
    9 |     "light": "Rosenthal et al. (1984), Seasonal affective disorder: A description of the syndrome and preliminary findings with light therapy, Archives of General Psychiatry 41:72-80. Seasonal light/mood only. Decorative evening lighting is not clinical therapy; coefficients are artistic assumptions.",
   10 |     "rng": "Numerical Recipes 32-bit LCG constants; portable game randomness, not cryptographic."
   11 |   },
   12 |   "clock": {
   13 |     "step_minutes": {
   14 |       "value": 15,
   15 |       "unit": "minute",
   16 |       "corridor": [
   17 |         15,
   18 |         15
   19 |       ],
   20 |       "source": "design"
   21 |     },
   22 |     "minutes_per_hour": {
   23 |       "value": 60,
   24 |       "unit": "minute/hour",
   25 |       "corridor": [
   26 |         60,
   27 |         60
   28 |       ],
   29 |       "source": "design"
   30 |     },
   31 |     "hours_per_day": {
   32 |       "value": 24,
   33 |       "unit": "hour/day",
   34 |       "corridor": [
   35 |         24,
   36 |         24
   37 |       ],
   38 |       "source": "design"
   39 |     },
   40 |     "days_per_week": {
   41 |       "value": 7,
   42 |       "unit": "day",
   43 |       "corridor": [
   44 |         7,
   45 |         7
   46 |       ],
   47 |       "source": "design"
   48 |     },
   49 |     "days_per_season": {
   50 |       "value": 21,
   51 |       "unit": "game day",
   52 |       "corridor": [
   53 |         1,
   54 |         365
   55 |       ],
   56 |       "source": "design"
   57 |     },
   58 |     "seasons": [
   59 |       "autumn",
   60 |       "winter",
   61 |       "spring",
   62 |       "summer"
   63 |     ],
   64 |     "phases": [
   65 |       {
   66 |         "name": "night",
   67 |         "start_hour": {
   68 |           "value": 0,
   69 |           "unit": "hour",
   70 |           "corridor": [
   71 |             0,
   72 |             24
   73 |           ],
   74 |           "source": "design"
   75 |         }
   76 |       },
   77 |       {
   78 |         "name": "morning",
   79 |         "start_hour": {
   80 |           "value": 6,
   81 |           "unit": "hour",
   82 |           "corridor": [
   83 |             0,
   84 |             24
   85 |           ],
   86 |           "source": "design"
   87 |         }
   88 |       },
   89 |       {
   90 |         "name": "day",
   91 |         "start_hour": {
   92 |           "value": 12,
   93 |           "unit": "hour",
   94 |           "corridor": [
   95 |             0,
   96 |             24
   97 |           ],
   98 |           "source": "design"
   99 |         }
  100 |       },
  101 |       {
  102 |         "name": "evening",
  103 |         "start_hour": {
  104 |           "value": 18,
  105 |           "unit": "hour",
  106 |           "corridor": [
  107 |             0,
  108 |             24
  109 |           ],
  110 |           "source": "design"
  111 |         }
  112 |       }
  113 |     ]
  114 |   },
  115 |   "initial": {
  116 |     "energy": {
  117 |       "value": 0.55,
  118 |       "unit": "fraction",
  119 |       "corridor": [
  120 |         0,
  121 |         1
  122 |       ],
  123 |       "source": "design"
  124 |     },
  125 |     "burnout": {
  126 |       "value": 0.4,
  127 |       "unit": "fraction",
  128 |       "corridor": [
  129 |         0,
  130 |         0.4
  131 |       ],
  132 |       "source": "design"
  133 |     },
  134 |     "mood": {
  135 |       "value": 0.5,
  136 |       "unit": "fraction",
  137 |       "corridor": [
  138 |         0,
  139 |         1
  140 |       ],
  141 |       "source": "design"
  142 |     },
  143 |     "habit": {
  144 |       "value": 0,
  145 |       "unit": "fraction",
  146 |       "corridor": [
  147 |         0,
  148 |         1
  149 |       ],
  150 |       "source": "design"
  151 |     },
  152 |     "practice_hours": {
  153 |       "value": 0,
  154 |       "unit": "hour",
  155 |       "corridor": [
  156 |         0,
  157 |         10000
  158 |       ],
  159 |       "source": "design"
  160 |     },
  161 |     "balance_cents": {
  162 |       "value": 20000,
  163 |       "unit": "rappen",
  164 |       "corridor": [
  165 |         0,
  166 |         10000000
  167 |       ],
  168 |       "source": "design"
  169 |     },
  170 |     "weather": "gray_wet"
  171 |   },
  172 |   "energy": {
  173 |     "burnout_penalty": {
  174 |       "value": 0.25,
  175 |       "unit": "fraction",
  176 |       "corridor": [
  177 |         0,
  178 |         1
  179 |       ],
  180 |       "source": "sleep"
  181 |     },
  182 |     "sleep_rate_per_hour": {
  183 |       "value": 0.35,
  184 |       "unit": "1/hour",
  185 |       "corridor": [
  186 |         0.2,
  187 |         0.6
  188 |       ],
  189 |       "source": "sleep"
  190 |     },
  191 |     "awake_rate_per_hour": {
  192 |       "value": 0.14,
  193 |       "unit": "1/hour",
  194 |       "corridor": [
  195 |         0.08,
  196 |         0.25
  197 |       ],
  198 |       "source": "sleep"
  199 |     }
  200 |   },
  201 |   "burnout": {
  202 |     "accumulation_per_hour": {
  203 |       "value": 0.006,
  204 |       "unit": "fraction/hour",
  205 |       "corridor": [
  206 |         0.005,
  207 |         0.009
  208 |       ],
  209 |       "source": "burnout"
  210 |     },
  211 |     "recovery_per_hour": {
  212 |       "value": 0.005,
  213 |       "unit": "1/hour",
  214 |       "corridor": [
  215 |         0.003,
  216 |         0.007
  217 |       ],
  218 |       "source": "burnout"
  219 |     },
  220 |     "threshold": {
  221 |       "value": 0.7,
  222 |       "unit": "fraction",
  223 |       "corridor": [
  224 |         0.7,
  225 |         0.8
  226 |       ],
  227 |       "source": "burnout"
  228 |     },
  229 |     "low_energy_threshold": {
  230 |       "value": 0.2,
  231 |       "unit": "fraction",
  232 |       "corridor": [
  233 |         0,
  234 |         1
  235 |       ],
  236 |       "source": "burnout"
  237 |     },
  238 |     "low_energy_load": {
  239 |       "value": 0.25,
  240 |       "unit": "fraction",
  241 |       "corridor": [
  242 |         0,
  243 |         1
  244 |       ],
  245 |       "source": "burnout"
  246 |     },
  247 |     "overload_max_days": {
  248 |       "value": 30,
  249 |       "unit": "day",
  250 |       "corridor": [
  251 |         30,
  252 |         40
  253 |       ],
  254 |       "source": "burnout"
  255 |     }
  256 |   },
  257 |   "mood": {
  258 |     "rate_per_hour": {
  259 |       "value": 0.25,
  260 |       "unit": "1/hour",
  261 |       "corridor": [
  262 |         0.1,
  263 |         0.5
  264 |       ],
  265 |       "source": "light"
  266 |     },
  267 |     "burnout_penalty": {
  268 |       "value": 0.2,
  269 |       "unit": "fraction",
  270 |       "corridor": [
  271 |         0,
  272 |         1
  273 |       ],
  274 |       "source": "light"
  275 |     }
  276 |   },
  277 |   "weather": {
  278 |     "golden_autumn": {
  279 |       "energy_shift": {
  280 |         "value": 0.1,
  281 |         "unit": "fraction",
  282 |         "corridor": [
  283 |           -0.4,
  284 |           0.4
  285 |         ],
  286 |         "source": "light"
  287 |       },
  288 |       "mood_shift": {
  289 |         "value": 0.2,
  290 |         "unit": "fraction",
  291 |         "corridor": [
  292 |           -0.4,
  293 |           0.4
  294 |         ],
  295 |         "source": "light"
  296 |       }
  297 |     },
  298 |     "gray_wet": {
  299 |       "energy_shift": {
  300 |         "value": -0.1,
  301 |         "unit": "fraction",
  302 |         "corridor": [
  303 |           -0.4,
  304 |           0.4
  305 |         ],
  306 |         "source": "light"
  307 |       },
  308 |       "mood_shift": {
  309 |         "value": -0.2,
  310 |         "unit": "fraction",
  311 |         "corridor": [
  312 |           -0.4,
  313 |           0.4
  314 |         ],
  315 |         "source": "light"
  316 |       }
  317 |     },
  318 |     "neutral": {
  319 |       "energy_shift": {
  320 |         "value": 0,
  321 |         "unit": "fraction",
  322 |         "corridor": [
  323 |           -0.4,
  324 |           0.4
  325 |         ],
  326 |         "source": "light"
  327 |       },
  328 |       "mood_shift": {
  329 |         "value": 0,
  330 |         "unit": "fraction",
  331 |         "corridor": [
  332 |           -0.4,
  333 |           0.4
  334 |         ],
  335 |         "source": "light"
  336 |       }
  337 |     }
  338 |   },
  339 |   "light": {
  340 |     "start_hour": {
  341 |       "value": 18,
  342 |       "unit": "hour",
  343 |       "corridor": [
  344 |         0,
  345 |         24
  346 |       ],
  347 |       "source": "light"
  348 |     },
  349 |     "end_hour": {
  350 |       "value": 24,
  351 |       "unit": "hour",
  352 |       "corridor": [
  353 |         0,
  354 |         24
  355 |       ],
  356 |       "source": "light"
  357 |     },
  358 |     "negative_weather_compensation": {
  359 |       "value": 0.5,
  360 |       "unit": "fraction",
  361 |       "corridor": [
  362 |         0.1,
  363 |         0.9
  364 |       ],
  365 |       "source": "light"
  366 |     }
  367 |   },
  368 |   "habits": {
  369 |     "days_to_automaticity": {
  370 |       "value": 66,
  371 |       "unit": "daily repetitions",
  372 |       "corridor": [
  373 |         18,
  374 |         254
  375 |       ],
  376 |       "source": "lally"
  377 |     },
  378 |     "asymptote_fraction": {
  379 |       "value": 0.95,
  380 |       "unit": "fraction",
  381 |       "corridor": [
  382 |         0.95,
  383 |         0.95
  384 |       ],
  385 |       "source": "lally"
  386 |     },
  387 |     "label_streak_days": {
  388 |       "value": 3,
  389 |       "unit": "day",
  390 |       "corridor": [
  391 |         2,
  392 |         10
  393 |       ],
  394 |       "source": "design"
  395 |     },
  396 |     "definitions": {
  397 |       "sleep": {
  398 |         "dose_hours": {
  399 |           "value": 8,
  400 |           "unit": "hour",
  401 |           "corridor": [
  402 |             0.25,
  403 |             10000
  404 |           ],
  405 |           "source": "design"
  406 |         },
  407 |         "label": "sleep_routine"
  408 |       },
  409 |       "exercise": {
  410 |         "dose_hours": {
  411 |           "value": 1,
  412 |           "unit": "hour",
  413 |           "corridor": [
  414 |             0.25,
  415 |             10000
  416 |           ],
  417 |           "source": "design"
  418 |         },
  419 |         "label": "athlete"
  420 |       },
  421 |       "alcohol": {
  422 |         "dose_hours": {
  423 |           "value": 1,
  424 |           "unit": "hour",
  425 |           "corridor": [
  426 |             0.25,
  427 |             10000
  428 |           ],
  429 |           "source": "design"
  430 |         },
  431 |         "label": "glass"
  432 |       },
  433 |       "screen": {
  434 |         "dose_hours": {
  435 |           "value": 2,
  436 |           "unit": "hour",
  437 |           "corridor": [
  438 |             0.25,
  439 |             10000
  440 |           ],
  441 |           "source": "design"
  442 |         },
  443 |         "label": "kettle"
  444 |       },
  445 |       "dream": {
  446 |         "dose_hours": {
  447 |           "value": 2,
  448 |           "unit": "hour",
  449 |           "corridor": [
  450 |             0.25,
  451 |             10000
  452 |           ],
  453 |           "source": "design"
  454 |         },
  455 |         "label": "creator"
  456 |       }
  457 |     }
  458 |   },
  459 |   "skills": {
  460 |     "scale_hours": {
  461 |       "value": 20,
  462 |       "unit": "hour",
  463 |       "corridor": [
  464 |         1,
  465 |         200
  466 |       ],
  467 |       "source": "practice"
  468 |     },
  469 |     "exponent": {
  470 |       "value": 0.6,
  471 |       "unit": "dimensionless",
  472 |       "corridor": [
  473 |         0.2,
  474 |         1
  475 |       ],
  476 |       "source": "practice"
  477 |     },
  478 |     "level_thresholds": [
  479 |       {
  480 |         "value": 0,
  481 |         "unit": "fraction",
  482 |         "corridor": [
  483 |           0,
  484 |           1
  485 |         ],
  486 |         "source": "practice"
  487 |       },
  488 |       {
  489 |         "value": 0.2,
  490 |         "unit": "fraction",
  491 |         "corridor": [
  492 |           0,
  493 |           1
  494 |         ],
  495 |         "source": "practice"
  496 |       },
  497 |       {
  498 |         "value": 0.4,
  499 |         "unit": "fraction",
  500 |         "corridor": [
  501 |           0,
  502 |           1
  503 |         ],
  504 |         "source": "practice"
  505 |       },
  506 |       {
  507 |         "value": 0.6,
  508 |         "unit": "fraction",
  509 |         "corridor": [
  510 |           0,
  511 |           1
  512 |         ],
  513 |         "source": "practice"
  514 |       },
  515 |       {
  516 |         "value": 0.8,
  517 |         "unit": "fraction",
  518 |         "corridor": [
  519 |           0,
  520 |           1
  521 |         ],
  522 |         "source": "practice"
  523 |       },
  524 |       {
  525 |         "value": 0.95,
  526 |         "unit": "fraction",
  527 |         "corridor": [
  528 |           0,
  529 |           1
  530 |         ],
  531 |         "source": "practice"
  532 |       }
  533 |     ],
  534 |     "names": [
  535 |       "german",
  536 |       "context",
  537 |       "code",
  538 |       "electronics",
  539 |       "social",
  540 |       "body",
  541 |       "focus"
  542 |     ]
  543 |   },
  544 |   "money": {
  545 |     "daily_cost_cents": {
  546 |       "value": 1800,
  547 |       "unit": "rappen/day",
  548 |       "corridor": [
  549 |         0,
  550 |         10000000
  551 |       ],
  552 |       "source": "design"
  553 |     },
  554 |     "support_cents": {
  555 |       "value": 90000,
  556 |       "unit": "rappen/payment",
  557 |       "corridor": [
  558 |         0,
  559 |         10000000
  560 |       ],
  561 |       "source": "design"
  562 |     },
  563 |     "support_period_days": {
  564 |       "value": 30,
  565 |       "unit": "game day",
  566 |       "corridor": [
  567 |         1,
  568 |         90
  569 |       ],
  570 |       "source": "design"
  571 |     },
  572 |     "distance_scale_cents": {
  573 |       "value": 100000,
  574 |       "unit": "rappen",
  575 |       "corridor": [
  576 |         1,
  577 |         10000000
  578 |       ],
  579 |       "source": "design"
  580 |     }
  581 |   },
  582 |   "rng": {
  583 |     "modulus": {
  584 |       "value": 4294967296,
  585 |       "unit": "count",
  586 |       "corridor": [
  587 |         4294967296,
  588 |         4294967296
  589 |       ],
  590 |       "source": "rng"
  591 |     },
  592 |     "multiplier": {
  593 |       "value": 1664525,
  594 |       "unit": "count",
  595 |       "corridor": [
  596 |         1664525,
  597 |         1664525
  598 |       ],
  599 |       "source": "rng"
  600 |     },
  601 |     "increment": {
  602 |       "value": 1013904223,
  603 |       "unit": "count",
  604 |       "corridor": [
  605 |         1013904223,
  606 |         1013904223
  607 |       ],
  608 |       "source": "rng"
  609 |     }
  610 |   },
  611 |   "actions": {
  612 |     "rest": {
  613 |       "energy_target": {
  614 |         "value": 0.7,
  615 |         "unit": "fraction",
  616 |         "corridor": [
  617 |           0,
  618 |           1
  619 |         ],
  620 |         "source": "design"
  621 |       },
  622 |       "load": {
  623 |         "value": 0,
  624 |         "unit": "fraction",
  625 |         "corridor": [
  626 |           0,
  627 |           1
  628 |         ],
  629 |         "source": "design"
  630 |       },
  631 |       "recovery": {
  632 |         "value": 0.5,
  633 |         "unit": "fraction",
  634 |         "corridor": [
  635 |           0,
  636 |           1
  637 |         ],
  638 |         "source": "design"
  639 |       },
  640 |       "mood_target": {
  641 |         "value": 0.55,
  642 |         "unit": "fraction",
  643 |         "corridor": [
  644 |           0,
  645 |           1
  646 |         ],
  647 |         "source": "design"
  648 |       },
  649 |       "skill": null,
  650 |       "habit": null,
  651 |       "wage_cents": {
  652 |         "value": 0,
  653 |         "unit": "rappen/tick",
  654 |         "corridor": [
  655 |           0,
  656 |           10000000
  657 |         ],
  658 |         "source": "design"
  659 |       },
  660 |       "cost_cents": {
  661 |         "value": 0,
  662 |         "unit": "rappen/tick",
  663 |         "corridor": [
  664 |           0,
  665 |           10000000
  666 |         ],
  667 |         "source": "design"
  668 |       },
  669 |       "morning_energy": {
  670 |         "value": 0,
  671 |         "unit": "fraction/repetition",
  672 |         "corridor": [
  673 |           -0.2,
  674 |           0.1
  675 |         ],
  676 |         "source": "design"
  677 |       },
  678 |       "morning_burnout": {
  679 |         "value": 0,
  680 |         "unit": "fraction/repetition",
  681 |         "corridor": [
  682 |           -0.03,
  683 |           0.05
  684 |         ],
  685 |         "source": "design"
  686 |       },
  687 |       "immediate_burnout": {
  688 |         "value": 0,
  689 |         "unit": "fraction/repetition",
  690 |         "corridor": [
  691 |           -0.03,
  692 |           0
  693 |         ],
  694 |         "source": "design"
  695 |       },
  696 |       "minimum_energy": {
  697 |         "value": 0,
  698 |         "unit": "fraction",
  699 |         "corridor": [
  700 |           0,
  701 |           1
  702 |         ],
  703 |         "source": "design"
  704 |       },
  705 |       "burnout_locked": false,
  706 |       "failure_base": {
  707 |         "value": 0,
  708 |         "unit": "fraction",
  709 |         "corridor": [
  710 |           0,
  711 |           1
  712 |         ],
  713 |         "source": "design"
  714 |       },
  715 |       "failure_burnout_factor": {
  716 |         "value": 0,
  717 |         "unit": "fraction",
  718 |         "corridor": [
  719 |           0,
  720 |           1
  721 |         ],
  722 |         "source": "design"
  723 |       },
  724 |       "skill_options": []
  725 |     },
  726 |     "sleep": {
  727 |       "energy_target": {
  728 |         "value": 1,
  729 |         "unit": "fraction",
  730 |         "corridor": [
  731 |           0,
  732 |           1
  733 |         ],
  734 |         "source": "design"
  735 |       },
  736 |       "load": {
  737 |         "value": 0,
  738 |         "unit": "fraction",
  739 |         "corridor": [
  740 |           0,
  741 |           1
  742 |         ],
  743 |         "source": "design"
  744 |       },
  745 |       "recovery": {
  746 |         "value": 1,
  747 |         "unit": "fraction",
  748 |         "corridor": [
  749 |           0,
  750 |           1
  751 |         ],
  752 |         "source": "design"
  753 |       },
  754 |       "mood_target": {
  755 |         "value": 0.55,
  756 |         "unit": "fraction",
  757 |         "corridor": [
  758 |           0,
  759 |           1
  760 |         ],
  761 |         "source": "design"
  762 |       },
  763 |       "skill": null,
  764 |       "habit": "sleep",
  765 |       "wage_cents": {
  766 |         "value": 0,
  767 |         "unit": "rappen/tick",
  768 |         "corridor": [
  769 |           0,
  770 |           10000000
  771 |         ],
  772 |         "source": "design"
  773 |       },
  774 |       "cost_cents": {
  775 |         "value": 0,
  776 |         "unit": "rappen/tick",
  777 |         "corridor": [
  778 |           0,
  779 |           10000000
  780 |         ],
  781 |         "source": "design"
  782 |       },
  783 |       "morning_energy": {
  784 |         "value": 0,
  785 |         "unit": "fraction/repetition",
  786 |         "corridor": [
  787 |           -0.2,
  788 |           0.1
  789 |         ],
  790 |         "source": "design"
  791 |       },
  792 |       "morning_burnout": {
  793 |         "value": 0,
  794 |         "unit": "fraction/repetition",
  795 |         "corridor": [
  796 |           -0.03,
  797 |           0.05
  798 |         ],
  799 |         "source": "design"
  800 |       },
  801 |       "immediate_burnout": {
  802 |         "value": 0,
  803 |         "unit": "fraction/repetition",
  804 |         "corridor": [
  805 |           -0.03,
  806 |           0
  807 |         ],
  808 |         "source": "design"
  809 |       },
  810 |       "minimum_energy": {
  811 |         "value": 0,
  812 |         "unit": "fraction",
  813 |         "corridor": [
  814 |           0,
  815 |           1
  816 |         ],
  817 |         "source": "design"
  818 |       },
  819 |       "burnout_locked": false,
  820 |       "failure_base": {
  821 |         "value": 0,
  822 |         "unit": "fraction",
  823 |         "corridor": [
  824 |           0,
  825 |           1
  826 |         ],
  827 |         "source": "design"
  828 |       },
  829 |       "failure_burnout_factor": {
  830 |         "value": 0,
  831 |         "unit": "fraction",
  832 |         "corridor": [
  833 |           0,
  834 |           1
  835 |         ],
  836 |         "source": "design"
  837 |       },
  838 |       "skill_options": []
  839 |     },
  840 |     "work": {
  841 |       "energy_target": {
  842 |         "value": 0.1,
  843 |         "unit": "fraction",
  844 |         "corridor": [
  845 |           0,
  846 |           1
  847 |         ],
  848 |         "source": "design"
  849 |       },
  850 |       "load": {
  851 |         "value": 1,
  852 |         "unit": "fraction",
  853 |         "corridor": [
  854 |           0,
  855 |           1
  856 |         ],
  857 |         "source": "design"
  858 |       },
  859 |       "recovery": {
  860 |         "value": 0,
  861 |         "unit": "fraction",
  862 |         "corridor": [
  863 |           0,
  864 |           1
  865 |         ],
  866 |         "source": "design"
  867 |       },
  868 |       "mood_target": {
  869 |         "value": 0.45,
  870 |         "unit": "fraction",
  871 |         "corridor": [
  872 |           0,
  873 |           1
  874 |         ],
  875 |         "source": "design"
  876 |       },
  877 |       "skill": "social",
  878 |       "habit": null,
  879 |       "wage_cents": {
  880 |         "value": 450,
  881 |         "unit": "rappen/tick",
  882 |         "corridor": [
  883 |           0,
  884 |           10000000
  885 |         ],
  886 |         "source": "design"
  887 |       },
  888 |       "cost_cents": {
  889 |         "value": 0,
  890 |         "unit": "rappen/tick",
  891 |         "corridor": [
  892 |           0,
  893 |           10000000
  894 |         ],
  895 |         "source": "design"
  896 |       },
  897 |       "morning_energy": {
  898 |         "value": 0,
  899 |         "unit": "fraction/repetition",
  900 |         "corridor": [
  901 |           -0.2,
  902 |           0.1
  903 |         ],
  904 |         "source": "design"
  905 |       },
  906 |       "morning_burnout": {
  907 |         "value": 0,
  908 |         "unit": "fraction/repetition",
  909 |         "corridor": [
  910 |           -0.03,
  911 |           0.05
  912 |         ],
  913 |         "source": "design"
  914 |       },
  915 |       "immediate_burnout": {
  916 |         "value": 0,
  917 |         "unit": "fraction/repetition",
  918 |         "corridor": [
  919 |           -0.03,
  920 |           0
  921 |         ],
  922 |         "source": "design"
  923 |       },
  924 |       "minimum_energy": {
  925 |         "value": 0,
  926 |         "unit": "fraction",
  927 |         "corridor": [
  928 |           0,
  929 |           1
  930 |         ],
  931 |         "source": "design"
  932 |       },
  933 |       "burnout_locked": false,
  934 |       "failure_base": {
  935 |         "value": 0,
  936 |         "unit": "fraction",
  937 |         "corridor": [
  938 |           0,
  939 |           1
  940 |         ],
  941 |         "source": "design"
  942 |       },
  943 |       "failure_burnout_factor": {
  944 |         "value": 0,
  945 |         "unit": "fraction",
  946 |         "corridor": [
  947 |           0,
  948 |           1
  949 |         ],
  950 |         "source": "design"
  951 |       },
  952 |       "skill_options": [
  953 |         "social"
  954 |       ]
  955 |     },
  956 |     "study": {
  957 |       "energy_target": {
  958 |         "value": 0.3,
  959 |         "unit": "fraction",
  960 |         "corridor": [
  961 |           0,
  962 |           1
  963 |         ],
  964 |         "source": "design"
  965 |       },
  966 |       "load": {
  967 |         "value": 0.6,
  968 |         "unit": "fraction",
  969 |         "corridor": [
  970 |           0,
  971 |           1
  972 |         ],
  973 |         "source": "design"
  974 |       },
  975 |       "recovery": {
  976 |         "value": 0,
  977 |         "unit": "fraction",
  978 |         "corridor": [
  979 |           0,
  980 |           1
  981 |         ],
  982 |         "source": "design"
  983 |       },
  984 |       "mood_target": {
  985 |         "value": 0.55,
  986 |         "unit": "fraction",
  987 |         "corridor": [
  988 |           0,
  989 |           1
  990 |         ],
  991 |         "source": "design"
  992 |       },
  993 |       "skill": "german",
  994 |       "habit": null,
  995 |       "wage_cents": {
  996 |         "value": 0,
  997 |         "unit": "rappen/tick",
  998 |         "corridor": [
  999 |           0,
 1000 |           10000000
 1001 |         ],
 1002 |         "source": "design"
 1003 |       },
 1004 |       "cost_cents": {
 1005 |         "value": 0,
 1006 |         "unit": "rappen/tick",
 1007 |         "corridor": [
 1008 |           0,
 1009 |           10000000
 1010 |         ],
 1011 |         "source": "design"
 1012 |       },
 1013 |       "morning_energy": {
 1014 |         "value": 0,
 1015 |         "unit": "fraction/repetition",
 1016 |         "corridor": [
 1017 |           -0.2,
 1018 |           0.1
 1019 |         ],
 1020 |         "source": "design"
 1021 |       },
 1022 |       "morning_burnout": {
 1023 |         "value": 0,
 1024 |         "unit": "fraction/repetition",
 1025 |         "corridor": [
 1026 |           -0.03,
 1027 |           0.05
 1028 |         ],
 1029 |         "source": "design"
 1030 |       },
 1031 |       "immediate_burnout": {
 1032 |         "value": 0,
 1033 |         "unit": "fraction/repetition",
 1034 |         "corridor": [
 1035 |           -0.03,
 1036 |           0
 1037 |         ],
 1038 |         "source": "design"
 1039 |       },
 1040 |       "minimum_energy": {
 1041 |         "value": 0.08,
 1042 |         "unit": "fraction",
 1043 |         "corridor": [
 1044 |           0,
 1045 |           1
 1046 |         ],
 1047 |         "source": "design"
 1048 |       },
 1049 |       "burnout_locked": true,
 1050 |       "failure_base": {
 1051 |         "value": 0,
 1052 |         "unit": "fraction",
 1053 |         "corridor": [
 1054 |           0,
 1055 |           1
 1056 |         ],
 1057 |         "source": "design"
 1058 |       },
 1059 |       "failure_burnout_factor": {
 1060 |         "value": 0.15,
 1061 |         "unit": "fraction",
 1062 |         "corridor": [
 1063 |           0,
 1064 |           1
 1065 |         ],
 1066 |         "source": "design"
 1067 |       },
 1068 |       "skill_options": [
 1069 |         "german",
 1070 |         "context",
 1071 |         "code",
 1072 |         "electronics",
 1073 |         "social",
 1074 |         "body",
 1075 |         "focus"
 1076 |       ]
 1077 |     },
 1078 |     "craft": {
 1079 |       "energy_target": {
 1080 |         "value": 0.25,
 1081 |         "unit": "fraction",
 1082 |         "corridor": [
 1083 |           0,
 1084 |           1
 1085 |         ],
 1086 |         "source": "design"
 1087 |       },
 1088 |       "load": {
 1089 |         "value": 0.7,
 1090 |         "unit": "fraction",
 1091 |         "corridor": [
 1092 |           0,
 1093 |           1
 1094 |         ],
 1095 |         "source": "design"
 1096 |       },
 1097 |       "recovery": {
 1098 |         "value": 0,
 1099 |         "unit": "fraction",
 1100 |         "corridor": [
 1101 |           0,
 1102 |           1
 1103 |         ],
 1104 |         "source": "design"
 1105 |       },
 1106 |       "mood_target": {
 1107 |         "value": 0.6,
 1108 |         "unit": "fraction",
 1109 |         "corridor": [
 1110 |           0,
 1111 |           1
 1112 |         ],
 1113 |         "source": "design"
 1114 |       },
 1115 |       "skill": "electronics",
 1116 |       "habit": null,
 1117 |       "wage_cents": {
 1118 |         "value": 0,
 1119 |         "unit": "rappen/tick",
 1120 |         "corridor": [
 1121 |           0,
 1122 |           10000000
 1123 |         ],
 1124 |         "source": "design"
 1125 |       },
 1126 |       "cost_cents": {
 1127 |         "value": 0,
 1128 |         "unit": "rappen/tick",
 1129 |         "corridor": [
 1130 |           0,
 1131 |           10000000
 1132 |         ],
 1133 |         "source": "design"
 1134 |       },
 1135 |       "morning_energy": {
 1136 |         "value": 0,
 1137 |         "unit": "fraction/repetition",
 1138 |         "corridor": [
 1139 |           -0.2,
 1140 |           0.1
 1141 |         ],
 1142 |         "source": "design"
 1143 |       },
 1144 |       "morning_burnout": {
 1145 |         "value": 0,
 1146 |         "unit": "fraction/repetition",
 1147 |         "corridor": [
 1148 |           -0.03,
 1149 |           0.05
 1150 |         ],
 1151 |         "source": "design"
 1152 |       },
 1153 |       "immediate_burnout": {
 1154 |         "value": 0,
 1155 |         "unit": "fraction/repetition",
 1156 |         "corridor": [
 1157 |           -0.03,
 1158 |           0
 1159 |         ],
 1160 |         "source": "design"
 1161 |       },
 1162 |       "minimum_energy": {
 1163 |         "value": 0.08,
 1164 |         "unit": "fraction",
 1165 |         "corridor": [
 1166 |           0,
 1167 |           1
 1168 |         ],
 1169 |         "source": "design"
 1170 |       },
 1171 |       "burnout_locked": true,
 1172 |       "failure_base": {
 1173 |         "value": 0,
 1174 |         "unit": "fraction",
 1175 |         "corridor": [
 1176 |           0,
 1177 |           1
 1178 |         ],
 1179 |         "source": "design"
 1180 |       },
 1181 |       "failure_burnout_factor": {
 1182 |         "value": 0.15,
 1183 |         "unit": "fraction",
 1184 |         "corridor": [
 1185 |           0,
 1186 |           1
 1187 |         ],
 1188 |         "source": "design"
 1189 |       },
 1190 |       "skill_options": [
 1191 |         "electronics"
 1192 |       ]
 1193 |     },
 1194 |     "dream": {
 1195 |       "energy_target": {
 1196 |         "value": 0.3,
 1197 |         "unit": "fraction",
 1198 |         "corridor": [
 1199 |           0,
 1200 |           1
 1201 |         ],
 1202 |         "source": "design"
 1203 |       },
 1204 |       "load": {
 1205 |         "value": 0.65,
 1206 |         "unit": "fraction",
 1207 |         "corridor": [
 1208 |           0,
 1209 |           1
 1210 |         ],
 1211 |         "source": "design"
 1212 |       },
 1213 |       "recovery": {
 1214 |         "value": 0,
 1215 |         "unit": "fraction",
 1216 |         "corridor": [
 1217 |           0,
 1218 |           1
 1219 |         ],
 1220 |         "source": "design"
 1221 |       },
 1222 |       "mood_target": {
 1223 |         "value": 0.75,
 1224 |         "unit": "fraction",
 1225 |         "corridor": [
 1226 |           0,
 1227 |           1
 1228 |         ],
 1229 |         "source": "design"
 1230 |       },
 1231 |       "skill": "code",
 1232 |       "habit": "dream",
 1233 |       "wage_cents": {
 1234 |         "value": 0,
 1235 |         "unit": "rappen/tick",
 1236 |         "corridor": [
 1237 |           0,
 1238 |           10000000
 1239 |         ],
 1240 |         "source": "design"
 1241 |       },
 1242 |       "cost_cents": {
 1243 |         "value": 0,
 1244 |         "unit": "rappen/tick",
 1245 |         "corridor": [
 1246 |           0,
 1247 |           10000000
 1248 |         ],
 1249 |         "source": "design"
 1250 |       },
 1251 |       "morning_energy": {
 1252 |         "value": 0,
 1253 |         "unit": "fraction/repetition",
 1254 |         "corridor": [
 1255 |           -0.2,
 1256 |           0.1
 1257 |         ],
 1258 |         "source": "design"
 1259 |       },
 1260 |       "morning_burnout": {
 1261 |         "value": 0,
 1262 |         "unit": "fraction/repetition",
 1263 |         "corridor": [
 1264 |           -0.03,
 1265 |           0.05
 1266 |         ],
 1267 |         "source": "design"
 1268 |       },
 1269 |       "immediate_burnout": {
 1270 |         "value": 0,
 1271 |         "unit": "fraction/repetition",
 1272 |         "corridor": [
 1273 |           -0.03,
 1274 |           0
 1275 |         ],
 1276 |         "source": "design"
 1277 |       },
 1278 |       "minimum_energy": {
 1279 |         "value": 0.08,
 1280 |         "unit": "fraction",
 1281 |         "corridor": [
 1282 |           0,
 1283 |           1
 1284 |         ],
 1285 |         "source": "design"
 1286 |       },
 1287 |       "burnout_locked": true,
 1288 |       "failure_base": {
 1289 |         "value": 0,
 1290 |         "unit": "fraction",
 1291 |         "corridor": [
 1292 |           0,
 1293 |           1
 1294 |         ],
 1295 |         "source": "design"
 1296 |       },
 1297 |       "failure_burnout_factor": {
 1298 |         "value": 0.15,
 1299 |         "unit": "fraction",
 1300 |         "corridor": [
 1301 |           0,
 1302 |           1
 1303 |         ],
 1304 |         "source": "design"
 1305 |       },
 1306 |       "skill_options": [
 1307 |         "code"
 1308 |       ]
 1309 |     },
 1310 |     "exercise": {
 1311 |       "energy_target": {
 1312 |         "value": 0.35,
 1313 |         "unit": "fraction",
 1314 |         "corridor": [
 1315 |           0,
 1316 |           1
 1317 |         ],
 1318 |         "source": "design"
 1319 |       },
 1320 |       "load": {
 1321 |         "value": 0.1,
 1322 |         "unit": "fraction",
 1323 |         "corridor": [
 1324 |           0,
 1325 |           1
 1326 |         ],
 1327 |         "source": "design"
 1328 |       },
 1329 |       "recovery": {
 1330 |         "value": 0.25,
 1331 |         "unit": "fraction",
 1332 |         "corridor": [
 1333 |           0,
 1334 |           1
 1335 |         ],
 1336 |         "source": "design"
 1337 |       },
 1338 |       "mood_target": {
 1339 |         "value": 0.65,
 1340 |         "unit": "fraction",
 1341 |         "corridor": [
 1342 |           0,
 1343 |           1
 1344 |         ],
 1345 |         "source": "design"
 1346 |       },
 1347 |       "skill": "body",
 1348 |       "habit": "exercise",
 1349 |       "wage_cents": {
 1350 |         "value": 0,
 1351 |         "unit": "rappen/tick",
 1352 |         "corridor": [
 1353 |           0,
 1354 |           10000000
 1355 |         ],
 1356 |         "source": "design"
 1357 |       },
 1358 |       "cost_cents": {
 1359 |         "value": 0,
 1360 |         "unit": "rappen/tick",
 1361 |         "corridor": [
 1362 |           0,
 1363 |           10000000
 1364 |         ],
 1365 |         "source": "design"
 1366 |       },
 1367 |       "morning_energy": {
 1368 |         "value": 0.1,
 1369 |         "unit": "fraction/repetition",
 1370 |         "corridor": [
 1371 |           -0.2,
 1372 |           0.1
 1373 |         ],
 1374 |         "source": "design"
 1375 |       },
 1376 |       "morning_burnout": {
 1377 |         "value": -0.03,
 1378 |         "unit": "fraction/repetition",
 1379 |         "corridor": [
 1380 |           -0.03,
 1381 |           0.05
 1382 |         ],
 1383 |         "source": "design"
 1384 |       },
 1385 |       "immediate_burnout": {
 1386 |         "value": 0,
 1387 |         "unit": "fraction/repetition",
 1388 |         "corridor": [
 1389 |           -0.03,
 1390 |           0
 1391 |         ],
 1392 |         "source": "design"
 1393 |       },
 1394 |       "minimum_energy": {
 1395 |         "value": 0,
 1396 |         "unit": "fraction",
 1397 |         "corridor": [
 1398 |           0,
 1399 |           1
 1400 |         ],
 1401 |         "source": "design"
 1402 |       },
 1403 |       "burnout_locked": false,
 1404 |       "failure_base": {
 1405 |         "value": 0,
 1406 |         "unit": "fraction",
 1407 |         "corridor": [
 1408 |           0,
 1409 |           1
 1410 |         ],
 1411 |         "source": "design"
 1412 |       },
 1413 |       "failure_burnout_factor": {
 1414 |         "value": 0,
 1415 |         "unit": "fraction",
 1416 |         "corridor": [
 1417 |           0,
 1418 |           1
 1419 |         ],
 1420 |         "source": "design"
 1421 |       },
 1422 |       "skill_options": [
 1423 |         "body"
 1424 |       ]
 1425 |     },
 1426 |     "alcohol": {
 1427 |       "energy_target": {
 1428 |         "value": 0.45,
 1429 |         "unit": "fraction",
 1430 |         "corridor": [
 1431 |           0,
 1432 |           1
 1433 |         ],
 1434 |         "source": "design"
 1435 |       },
 1436 |       "load": {
 1437 |         "value": 0.1,
 1438 |         "unit": "fraction",
 1439 |         "corridor": [
 1440 |           0,
 1441 |           1
 1442 |         ],
 1443 |         "source": "design"
 1444 |       },
 1445 |       "recovery": {
 1446 |         "value": 0,
 1447 |         "unit": "fraction",
 1448 |         "corridor": [
 1449 |           0,
 1450 |           1
 1451 |         ],
 1452 |         "source": "design"
 1453 |       },
 1454 |       "mood_target": {
 1455 |         "value": 0.85,
 1456 |         "unit": "fraction",
 1457 |         "corridor": [
 1458 |           0,
 1459 |           1
 1460 |         ],
 1461 |         "source": "design"
 1462 |       },
 1463 |       "skill": null,
 1464 |       "habit": "alcohol",
 1465 |       "wage_cents": {
 1466 |         "value": 0,
 1467 |         "unit": "rappen/tick",
 1468 |         "corridor": [
 1469 |           0,
 1470 |           10000000
 1471 |         ],
 1472 |         "source": "design"
 1473 |       },
 1474 |       "cost_cents": {
 1475 |         "value": 150,
 1476 |         "unit": "rappen/tick",
 1477 |         "corridor": [
 1478 |           0,
 1479 |           10000000
 1480 |         ],
 1481 |         "source": "design"
 1482 |       },
 1483 |       "morning_energy": {
 1484 |         "value": -0.2,
 1485 |         "unit": "fraction/repetition",
 1486 |         "corridor": [
 1487 |           -0.2,
 1488 |           0.1
 1489 |         ],
 1490 |         "source": "design"
 1491 |       },
 1492 |       "morning_burnout": {
 1493 |         "value": 0.05,
 1494 |         "unit": "fraction/repetition",
 1495 |         "corridor": [
 1496 |           -0.03,
 1497 |           0.05
 1498 |         ],
 1499 |         "source": "design"
 1500 |       },
 1501 |       "immediate_burnout": {
 1502 |         "value": -0.03,
 1503 |         "unit": "fraction/repetition",
 1504 |         "corridor": [
 1505 |           -0.03,
 1506 |           0
 1507 |         ],
 1508 |         "source": "design"
 1509 |       },
 1510 |       "minimum_energy": {
 1511 |         "value": 0,
 1512 |         "unit": "fraction",
 1513 |         "corridor": [
 1514 |           0,
 1515 |           1
 1516 |         ],
 1517 |         "source": "design"
 1518 |       },
 1519 |       "burnout_locked": false,
 1520 |       "failure_base": {
 1521 |         "value": 0,
 1522 |         "unit": "fraction",
 1523 |         "corridor": [
 1524 |           0,
 1525 |           1
 1526 |         ],
 1527 |         "source": "design"
 1528 |       },
 1529 |       "failure_burnout_factor": {
 1530 |         "value": 0,
 1531 |         "unit": "fraction",
 1532 |         "corridor": [
 1533 |           0,
 1534 |           1
 1535 |         ],
 1536 |         "source": "design"
 1537 |       },
 1538 |       "skill_options": []
 1539 |     },
 1540 |     "screen": {
 1541 |       "energy_target": {
 1542 |         "value": 0.5,
 1543 |         "unit": "fraction",
 1544 |         "corridor": [
 1545 |           0,
 1546 |           1
 1547 |         ],
 1548 |         "source": "design"
 1549 |       },
 1550 |       "load": {
 1551 |         "value": 0.12,
 1552 |         "unit": "fraction",
 1553 |         "corridor": [
 1554 |           0,
 1555 |           1
 1556 |         ],
 1557 |         "source": "design"
 1558 |       },
 1559 |       "recovery": {
 1560 |         "value": 0.1,
 1561 |         "unit": "fraction",
 1562 |         "corridor": [
 1563 |           0,
 1564 |           1
 1565 |         ],
 1566 |         "source": "design"
 1567 |       },
 1568 |       "mood_target": {
 1569 |         "value": 0.65,
 1570 |         "unit": "fraction",
 1571 |         "corridor": [
 1572 |           0,
 1573 |           1
 1574 |         ],
 1575 |         "source": "design"
 1576 |       },
 1577 |       "skill": null,
 1578 |       "habit": "screen",
 1579 |       "wage_cents": {
 1580 |         "value": 0,
 1581 |         "unit": "rappen/tick",
 1582 |         "corridor": [
 1583 |           0,
 1584 |           10000000
 1585 |         ],
 1586 |         "source": "design"
 1587 |       },
 1588 |       "cost_cents": {
 1589 |         "value": 0,
 1590 |         "unit": "rappen/tick",
 1591 |         "corridor": [
 1592 |           0,
 1593 |           10000000
 1594 |         ],
 1595 |         "source": "design"
 1596 |       },
 1597 |       "morning_energy": {
 1598 |         "value": -0.05,
 1599 |         "unit": "fraction/repetition",
 1600 |         "corridor": [
 1601 |           -0.2,
 1602 |           0.1
 1603 |         ],
 1604 |         "source": "design"
 1605 |       },
 1606 |       "morning_burnout": {
 1607 |         "value": 0,
 1608 |         "unit": "fraction/repetition",
 1609 |         "corridor": [
 1610 |           -0.03,
 1611 |           0.05
 1612 |         ],
 1613 |         "source": "design"
 1614 |       },
 1615 |       "immediate_burnout": {
 1616 |         "value": 0,
 1617 |         "unit": "fraction/repetition",
 1618 |         "corridor": [
 1619 |           -0.03,
 1620 |           0
 1621 |         ],
 1622 |         "source": "design"
 1623 |       },
 1624 |       "minimum_energy": {
 1625 |         "value": 0,
 1626 |         "unit": "fraction",
 1627 |         "corridor": [
 1628 |           0,
 1629 |           1
 1630 |         ],
 1631 |         "source": "design"
 1632 |       },
 1633 |       "burnout_locked": false,
 1634 |       "failure_base": {
 1635 |         "value": 0,
 1636 |         "unit": "fraction",
 1637 |         "corridor": [
 1638 |           0,
 1639 |           1
 1640 |         ],
 1641 |         "source": "design"
 1642 |       },
 1643 |       "failure_burnout_factor": {
 1644 |         "value": 0,
 1645 |         "unit": "fraction",
 1646 |         "corridor": [
 1647 |           0,
 1648 |           1
 1649 |         ],
 1650 |         "source": "design"
 1651 |       },
 1652 |       "skill_options": []
 1653 |     }
 1654 |   },
 1655 |   "validation": {
 1656 |     "seed": {
 1657 |       "value": 43615,
 1658 |       "unit": "uint32",
 1659 |       "corridor": [
 1660 |         0,
 1661 |         4294967295
 1662 |       ],
 1663 |       "source": "design"
 1664 |     },
 1665 |     "random_runs": {
 1666 |       "value": 10000,
 1667 |       "unit": "count",
 1668 |       "corridor": [
 1669 |         10000,
 1670 |         10000
 1671 |       ],
 1672 |       "source": "design"
 1673 |     },
 1674 |     "random_max_steps": {
 1675 |       "value": 24,
 1676 |       "unit": "count",
 1677 |       "corridor": [
 1678 |         24,
 1679 |         24
 1680 |       ],
 1681 |       "source": "design"
 1682 |     },
 1683 |     "tolerance": {
 1684 |       "value": 1e-09,
 1685 |       "unit": "absolute",
 1686 |       "corridor": [
 1687 |         1e-09,
 1688 |         1e-09
 1689 |       ],
 1690 |       "source": "design"
 1691 |     },
 1692 |     "equilibrium_steps": {
 1693 |       "value": 10000,
 1694 |       "unit": "count",
 1695 |       "corridor": [
 1696 |         10000,
 1697 |         10000
 1698 |       ],
 1699 |       "source": "design"
 1700 |     },
 1701 |     "scenario_days": {
 1702 |       "value": 30,
 1703 |       "unit": "count",
 1704 |       "corridor": [
 1705 |         30,
 1706 |         30
 1707 |       ],
 1708 |       "source": "design"
 1709 |     },
 1710 |     "trajectory_min_distance": {
 1711 |       "value": 0.08,
 1712 |       "unit": "normalized RMS",
 1713 |       "corridor": [
 1714 |         0.01,
 1715 |         0.2
 1716 |       ],
 1717 |       "source": "design"
 1718 |     }
 1719 |   },
 1720 |   "scenarios": {
 1721 |     "workaholic": {
 1722 |       "light": false,
 1723 |       "schedule": [
 1724 |         {
 1725 |           "start": {
 1726 |             "value": 0,
 1727 |             "unit": "hour",
 1728 |             "corridor": [
 1729 |               0,
 1730 |               24
 1731 |             ],
 1732 |             "source": "design"
 1733 |           },
 1734 |           "end": {
 1735 |             "value": 6,
 1736 |             "unit": "hour",
 1737 |             "corridor": [
 1738 |               0,
 1739 |               24
 1740 |             ],
 1741 |             "source": "design"
 1742 |           },
 1743 |           "action": "sleep"
 1744 |         },
 1745 |         {
 1746 |           "start": {
 1747 |             "value": 6,
 1748 |             "unit": "hour",
 1749 |             "corridor": [
 1750 |               0,
 1751 |               24
 1752 |             ],
 1753 |             "source": "design"
 1754 |           },
 1755 |           "end": {
 1756 |             "value": 22,
 1757 |             "unit": "hour",
 1758 |             "corridor": [
 1759 |               0,
 1760 |               24
 1761 |             ],
 1762 |             "source": "design"
 1763 |           },
 1764 |           "action": "work"
 1765 |         },
 1766 |         {
 1767 |           "start": {
 1768 |             "value": 22,
 1769 |             "unit": "hour",
 1770 |             "corridor": [
 1771 |               0,
 1772 |               24
 1773 |             ],
 1774 |             "source": "design"
 1775 |           },
 1776 |           "end": {
 1777 |             "value": 24,
 1778 |             "unit": "hour",
 1779 |             "corridor": [
 1780 |               0,
 1781 |               24
 1782 |             ],
 1783 |             "source": "design"
 1784 |           },
 1785 |           "action": "dream"
 1786 |         }
 1787 |       ]
 1788 |     },
 1789 |     "balanced": {
 1790 |       "light": true,
 1791 |       "schedule": [
 1792 |         {
 1793 |           "start": {
 1794 |             "value": 0,
 1795 |             "unit": "hour",
 1796 |             "corridor": [
 1797 |               0,
 1798 |               24
 1799 |             ],
 1800 |             "source": "design"
 1801 |           },
 1802 |           "end": {
 1803 |             "value": 7,
 1804 |             "unit": "hour",
 1805 |             "corridor": [
 1806 |               0,
 1807 |               24
 1808 |             ],
 1809 |             "source": "design"
 1810 |           },
 1811 |           "action": "sleep"
 1812 |         },
 1813 |         {
 1814 |           "start": {
 1815 |             "value": 7,
 1816 |             "unit": "hour",
 1817 |             "corridor": [
 1818 |               0,
 1819 |               24
 1820 |             ],
 1821 |             "source": "design"
 1822 |           },
 1823 |           "end": {
 1824 |             "value": 8,
 1825 |             "unit": "hour",
 1826 |             "corridor": [
 1827 |               0,
 1828 |               24
 1829 |             ],
 1830 |             "source": "design"
 1831 |           },
 1832 |           "action": "exercise"
 1833 |         },
 1834 |         {
 1835 |           "start": {
 1836 |             "value": 8,
 1837 |             "unit": "hour",
 1838 |             "corridor": [
 1839 |               0,
 1840 |               24
 1841 |             ],
 1842 |             "source": "design"
 1843 |           },
 1844 |           "end": {
 1845 |             "value": 12,
 1846 |             "unit": "hour",
 1847 |             "corridor": [
 1848 |               0,
 1849 |               24
 1850 |             ],
 1851 |             "source": "design"
 1852 |           },
 1853 |           "action": "work"
 1854 |         },
 1855 |         {
 1856 |           "start": {
 1857 |             "value": 12,
 1858 |             "unit": "hour",
 1859 |             "corridor": [
 1860 |               0,
 1861 |               24
 1862 |             ],
 1863 |             "source": "design"
 1864 |           },
 1865 |           "end": {
 1866 |             "value": 13,
 1867 |             "unit": "hour",
 1868 |             "corridor": [
 1869 |               0,
 1870 |               24
 1871 |             ],
 1872 |             "source": "design"
 1873 |           },
 1874 |           "action": "rest"
 1875 |         },
 1876 |         {
 1877 |           "start": {
 1878 |             "value": 13,
 1879 |             "unit": "hour",
 1880 |             "corridor": [
 1881 |               0,
 1882 |               24
 1883 |             ],
 1884 |             "source": "design"
 1885 |           },
 1886 |           "end": {
 1887 |             "value": 16,
 1888 |             "unit": "hour",
 1889 |             "corridor": [
 1890 |               0,
 1891 |               24
 1892 |             ],
 1893 |             "source": "design"
 1894 |           },
 1895 |           "action": "study"
 1896 |         },
 1897 |         {
 1898 |           "start": {
 1899 |             "value": 16,
 1900 |             "unit": "hour",
 1901 |             "corridor": [
 1902 |               0,
 1903 |               24
 1904 |             ],
 1905 |             "source": "design"
 1906 |           },
 1907 |           "end": {
 1908 |             "value": 18,
 1909 |             "unit": "hour",
 1910 |             "corridor": [
 1911 |               0,
 1912 |               24
 1913 |             ],
 1914 |             "source": "design"
 1915 |           },
 1916 |           "action": "dream"
 1917 |         },
 1918 |         {
 1919 |           "start": {
 1920 |             "value": 18,
 1921 |             "unit": "hour",
 1922 |             "corridor": [
 1923 |               0,
 1924 |               24
 1925 |             ],
 1926 |             "source": "design"
 1927 |           },
 1928 |           "end": {
 1929 |             "value": 22,
 1930 |             "unit": "hour",
 1931 |             "corridor": [
 1932 |               0,
 1933 |               24
 1934 |             ],
 1935 |             "source": "design"
 1936 |           },
 1937 |           "action": "rest"
 1938 |         },
 1939 |         {
 1940 |           "start": {
 1941 |             "value": 22,
 1942 |             "unit": "hour",
 1943 |             "corridor": [
 1944 |               0,
 1945 |               24
 1946 |             ],
 1947 |             "source": "design"
 1948 |           },
 1949 |           "end": {
 1950 |             "value": 24,
 1951 |             "unit": "hour",
 1952 |             "corridor": [
 1953 |               0,
 1954 |               24
 1955 |             ],
 1956 |             "source": "design"
 1957 |           },
 1958 |           "action": "sleep"
 1959 |         }
 1960 |       ]
 1961 |     },
 1962 |     "procrastinator": {
 1963 |       "light": false,
 1964 |       "schedule": [
 1965 |         {
 1966 |           "start": {
 1967 |             "value": 0,
 1968 |             "unit": "hour",
 1969 |             "corridor": [
 1970 |               0,
 1971 |               24
 1972 |             ],
 1973 |             "source": "design"
 1974 |           },
 1975 |           "end": {
 1976 |             "value": 3,
 1977 |             "unit": "hour",
 1978 |             "corridor": [
 1979 |               0,
 1980 |               24
 1981 |             ],
 1982 |             "source": "design"
 1983 |           },
 1984 |           "action": "screen"
 1985 |         },
 1986 |         {
 1987 |           "start": {
 1988 |             "value": 3,
 1989 |             "unit": "hour",
 1990 |             "corridor": [
 1991 |               0,
 1992 |               24
 1993 |             ],
 1994 |             "source": "design"
 1995 |           },
 1996 |           "end": {
 1997 |             "value": 10,
 1998 |             "unit": "hour",
 1999 |             "corridor": [
 2000 |               0,
 2001 |               24
 2002 |             ],
 2003 |             "source": "design"
 2004 |           },
 2005 |           "action": "sleep"
 2006 |         },
 2007 |         {
 2008 |           "start": {
 2009 |             "value": 10,
 2010 |             "unit": "hour",
 2011 |             "corridor": [
 2012 |               0,
 2013 |               24
 2014 |             ],
 2015 |             "source": "design"
 2016 |           },
 2017 |           "end": {
 2018 |             "value": 12,
 2019 |             "unit": "hour",
 2020 |             "corridor": [
 2021 |               0,
 2022 |               24
 2023 |             ],
 2024 |             "source": "design"
 2025 |           },
 2026 |           "action": "rest"
 2027 |         },
 2028 |         {
 2029 |           "start": {
 2030 |             "value": 12,
 2031 |             "unit": "hour",
 2032 |             "corridor": [
 2033 |               0,
 2034 |               24
 2035 |             ],
 2036 |             "source": "design"
 2037 |           },
 2038 |           "end": {
 2039 |             "value": 18,
 2040 |             "unit": "hour",
 2041 |             "corridor": [
 2042 |               0,
 2043 |               24
 2044 |             ],
 2045 |             "source": "design"
 2046 |           },
 2047 |           "action": "screen"
 2048 |         },
 2049 |         {
 2050 |           "start": {
 2051 |             "value": 18,
 2052 |             "unit": "hour",
 2053 |             "corridor": [
 2054 |               0,
 2055 |               24
 2056 |             ],
 2057 |             "source": "design"
 2058 |           },
 2059 |           "end": {
 2060 |             "value": 20,
 2061 |             "unit": "hour",
 2062 |             "corridor": [
 2063 |               0,
 2064 |               24
 2065 |             ],
 2066 |             "source": "design"
 2067 |           },
 2068 |           "action": "alcohol"
 2069 |         },
 2070 |         {
 2071 |           "start": {
 2072 |             "value": 20,
 2073 |             "unit": "hour",
 2074 |             "corridor": [
 2075 |               0,
 2076 |               24
 2077 |             ],
 2078 |             "source": "design"
 2079 |           },
 2080 |           "end": {
 2081 |             "value": 24,
 2082 |             "unit": "hour",
 2083 |             "corridor": [
 2084 |               0,
 2085 |               24
 2086 |             ],
 2087 |             "source": "design"
 2088 |           },
 2089 |           "action": "screen"
 2090 |         }
 2091 |       ]
 2092 |     }
 2093 |   },
 2094 |   "scenario_weather_cycle": [
 2095 |     "gray_wet",
 2096 |     "golden_autumn",
 2097 |     "neutral",
 2098 |     "gray_wet"
 2099 |   ]
 2100 | }
````
