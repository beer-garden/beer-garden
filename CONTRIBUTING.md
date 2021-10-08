# Contributing to Beergarden

Since many people have many different uses for Beergarden, it makes sense that
you may need functionality that's not currently supported. If that's the case,
and you think you can add the functionality yourself, feel free! Here's the
easiest way to make changes:

1. Fork the project
2. Clone your project fork
   (`git clone https://github.com/<username>/beer-garden.git`)
3. Create a new branch (`git checkout -b issue/1234-my-amazing-feature`)
4. Commit your changes (`git commit -m "#1234 - It's done!"`)
5. Push to the branch (`git push origin issue/1234-my-amazing-feature`)
6. Create a
   [new pull request](https://github.com/beer-garden/beer-garden/compare) in
   Github

We want to do everything we can to make sure we're delivering robust software.
So we just ask that before submitting a merge request you:

1. Make sure all the existing tests work (`make test` from the `src/app`
   directory)
2. Create new tests for the functionality you've created. These should work too
   :)

Finally, **thank you for your contribution!** Your help is very much appreciated
by the Beergarden developers and users.
