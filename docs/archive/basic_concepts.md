
Echo is a application used to abstract the process of notification campaign management. Specifically in the contetxt of an enterprise that has multiple internal teams which offer services to other internal teams.  Echo provides a unified interface to manage notification campaigns, track their performance, and generate reports.

Specifically Echo provides the following features:
- Campaign Management: Create, schedule, and manage notification campaigns.
- Template Management: Create and manage notification templates per campaign.
- Escalation Management: Define and manage escalation policies for notification campaigns.
- Minimally Invasive: Echo is designed to be minimally invasive, allowing teams to integrate it into their data sources with no schema changes.
- Leverage Existing Tools: Echo leverages existing tools and services with the Campaign Owning Team (COT) for metadata management - your data is your data; Echo minimally requires read access to certain fields.
- Extensible Architecture: Echo is built with an extensible architecture, allowing for easy integration of new notification channels and data sources.
-

Enhancements:
- Reporting and Analytics: Generate reports and analytics on campaign performance.


Terms:
Campaign - A campaign is defined by a set of "reviewable items" that need to be verified/updated/confirmed by a set of users, usually derived from a reviewable item's contacts.  A campaign defines the set of reviewable items that are notified with the set of same defined cycles.

Reviewable Item - A reviewable item is an entity that needs to be reviewed/verified/confirmed by a user.  Examples of reviewable items are: a service, a database, a server, a document, etc.  A reviewable item is associated with a set of contacts that are responsible for reviewing it.

Cycle - A cycle is series of notifications that are sent to the contacts associated with the reviewable item.  A cycle is defined by a start date, an end date, a set of escalation policies and a set of notification templates.

Notification - A notification is a message that is sent to a contact.  A notification is defined by a template, a recipient and template metadata.

Echo - A management system for scheduling and managing escalating notification campaigns.

Technologies:
- Backend: Echo's backend is built using Python and FastAPI, providing a RESTful API for managing campaigns, templates, and notifications.
- Database: Echo uses PostgreSQL for storing campaign data, templates, and notification history.
- API first design principles
- I want minimal front end to start, maybe just a dashboard to view campaigns and their status.  The main interaction with Echo will be through the API, allowing teams to integrate it into their existing workflows and tools.
- This will run in AWS, leveraging ECS, with possibility to use other AWS services it makes sense (e.g., S3 for storing templates, CloudWatch for logging and monitoring, etc.).
- Ask questions about the tech stack and design choices to ensure that the architecture is scalable, maintainable, and meets the needs of the users.
- I want well-architected code that follows best practices for software development, including modular design, separation of concerns, and adherence to SOLID principles.
- I want to implement a robust testing strategy, including unit tests, integration tests, and end-to-end tests to ensure the reliability and stability of the application.
- I want to implement a CI/CD pipeline to automate the testing and deployment process, ensuring that new features and bug fixes are delivered quickly and reliably to users.

I want to use uv for python
I want to have make file for common tasks (e.g., running the server, running tests, etc.) to simplify development and ensure consistency across the team.
Some example data in examples/
