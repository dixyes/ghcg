
textVert = "2024";
textHoriz = "@twose";

module card(protrusion = true) {
    color("#fff8")
    translate([-50, 10, 10])
        rotate([60, 0, 0])
            union() {
                linear_extrude(2.1)
                    hull() {
                        translate([0, 0, 0])
                            circle(r = 8);
                        translate([200, 0, 0])
                            circle(r = 8);
                        translate([200, 40, 0])
                            circle(r = 8);
                        translate([0, 40, 0])
                            circle(r = 8);
                    }
                if (protrusion)
                    translate([0, -1, 0])
                        cube([200, 40, 100]);

            }
}

module vertLetters() {
    color("black")
    union() {
        difference() {
            union() {
                translate([0, 15, 1])
                    rotate([90, 0, 0])
                        linear_extrude(height = 15)
                            text(textVert, size = 15, font = "Source Code Pro");
            }
            card();
        }
        linear_extrude(1)
            hull() {
                translate([5, 0, 0])
                    circle(r = 8);
                translate([5, 12, 0])
                    circle(r = 8);
                translate([65, 12, 0])
                    circle(r = 8);
                translate([65, 0, 0])
                    circle(r = 8);
            }
    }
}

module horizLetters() {
    color("white")
        difference() {
            union() {
                translate([5, -10, 0])
                    linear_extrude(height = 2)
                        text(textHoriz, size = 15, font = "Source Code Pro");
            }
            vertLetters();
        }
}

vertLetters();

horizLetters();

// card(protrusion = false);
