from sklearn.pipeline import Pipeline
import src.data.pipelines as ppl


preprocessing_pipeline = Pipeline(
    [
        ('cols_filter', ppl.ColumnsFilter(all_except=['body', 'label'])),
        ('nan_filter', ppl.EmptyValuesFilter(['body'])),
        ('dup_filter', ppl.DuplicatesFilter('body')),
        ('text_preprocess', ppl.TextPreprocessor('body')),
        ('size_filter', ppl.ArticlesSizeFilter('body', 100, 6000)),
        ('sent_len_filter', ppl.ArticlesSentenceLengthFilter('body', 8, 50)),
        ('lang_filter', ppl.ArticlesLanguageFilter('body', 'en')),
    ]
)


def preprocess_data(dataframes):
    """
    Function to preprocess the data using Pipelines.

    Following transformations are performed:
    1. Filter columns that are not needed.
    2. Filtering samples by size of articles (lower and upper boundary).
    3. Filtering samples by language of articles - only english will
        be used.
    4. Text preprocessing (e.g. removing special characters, tags, etc),
        making text lowercase, etc.

    :param dataframes: list, dataframes to be preprocessed.
    :return: list, preprocessed dataframes.
    """
    return [
        preprocessing_pipeline.transform(dataframe)
        for dataframe in dataframes
    ]
