(import [system.plugins.plugin [PluginObject]])

(defclass HyTestPlugin [PluginObject]
    "This is a docstring"

    [
        [setup (fn [self]
            (apply self.commands.register_command
                [
                    "hyexample"
                    self.example_command
                    self
                ]
                {
                    ; "permission" "hytest.hyexample"
                    "aliases" ["hyexample2"]
                    "default" True
                }
            )
        )]

        [example-command (fn
            [self protocol caller source command raw_args args]

            (if (is args nil)
                (setv args (.split raw_args))
            )

            (.respond source (+ "Hello, world! You ran the " command " command!"))

            (.respond caller (+ "Raw arguments: " raw_args))
            (.respond caller (+ "Parsed arguments: " (str args)))

            (.send_msg protocol source "Message through the protocol!")
        )]

    ]
)
