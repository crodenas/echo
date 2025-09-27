# getting some ideas

I want to build an enterprise software system named ECHO.

Multiple teams maintain various resources services for application teams. Each item has a set of contacts.  All will all have standard set of contacts.

I want to design ECHO so that a team can bring their resource inventory, with contacts for each, and have ECHO send notifications to users to verify or update contacts and metadata on a regular cycle.

I want to require as few changes to the infrastructure team's data to make it work with ECHO.

I want to talk about the interface between ECHO datastore and the infrastructure team's database that holds their inventory. When a user is notified to verify contacts, where should that be done? I'd like the source of truth to remain with the owning Team and simply position ECHO as an available tool to manage this process for teams.  ECHO will have its own database that will be used to manage its state and not make changes to other team's data directly.  I envision ECHO will send notifications to users to verify metadata and that will direct them to make updates in the source of truth.  But how should ECHO come to know that a record in their system was updated or confirmed while putting as little effort on the other team as possible?


The Campaign object should capture the frequency of the the start of each cycle and notifications in each cycle.
