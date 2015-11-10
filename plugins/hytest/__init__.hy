; Please note that we're using the stable version of Hy (0.11.0), not the latest git master.
; You can find the docs here: http://docs.hylang.org/en/stable/

(import [system.plugins.plugin [PluginObject]])

(defclass HyTestPlugin [PluginObject]
    "Example plugin object - written in Hy"

    [
        [setup (fn [self]
            "Called when the plugin is loaded. Performs initial setup."

            ; Register the command in our system
            (apply self.commands.register_command
                [
                    "hyexample"  ; The name of the command
                    self.example_command  ; The command's function
                    self  ; This plugin
                ]
                {
                    ; "permission" "hytest.hyexample"  ; Required permission for command
                    "aliases" ["hyexample2"]  ; Aliases for this command
                    "default" True  ; Whether this command should be available to all
                }
            )
        )]

        [example-command (fn
            [self protocol caller source command raw_args args]
            "Command handler for the hyexample command"

            (if (is args nil)
                ; You'll probably always want this, so you always have
                ; arguments if quote-parsing fails
                (setv args (.split raw_args))
            )

            ; Send to the channel
            (.respond source (+ "Hello, world! You ran the " command " command!"))

            ; Send to the user that ran the command
            (.respond caller (+ "Raw arguments: " raw_args))
            (.respond caller (+ "Parsed arguments: " (str args)))

            ; Send directly to the protocol
            (.send_msg protocol source "Message through the protocol!")
        )]

    ]
)
