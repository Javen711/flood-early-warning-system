# ML (model training & experimentation)

Not started yet -- this gets built out in **Phase 4** of the development roadmap
(training and serializing the Random Forest flood-risk model). Suggested structure
once you get there:

    ml/
      data/            # raw and processed training data (gitignored)
      notebooks/        # exploration notebooks
      train_model.py    # training script
      model.pkl          # serialized model (gitignored, regenerate via train_model.py)
