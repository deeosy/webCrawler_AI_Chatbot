import codetrain as ct
from jobs import (
    URLInputJob,
    ValidateURLJob,
    ScrapeJob,
    IndexJob,
    ValidateContextJob,
    RetrieveJob,
    GenerateAnswerJob,
    DeclineJob,
)


def create_indexing_hustle():
    """Create hustle for indexing URLs."""
    url_input = URLInputJob()
    validate = ValidateURLJob()
    scrape = ScrapeJob()
    index = IndexJob()

    url_input >> validate >> scrape >> index

    return ct.Hustle(start=url_input)


def create_chat_hustle():
    """Create hustle for answering queries."""
    validate = ValidateContextJob()
    retrieve = RetrieveJob()
    generate = GenerateAnswerJob()
    decline = DeclineJob()

    validate - "retrieve" >> retrieve
    retrieve - "generate" >> generate
    validate - "decline" >> decline

    return ct.Hustle(start=validate)
