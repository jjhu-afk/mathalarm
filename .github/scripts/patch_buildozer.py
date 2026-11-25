"""Enable p4a's application XML option in the Buildozer container.

python-for-android supports --extra-manifest-application-xml, while the
current Buildozer frontend does not expose the matching spec setting.
"""

from pathlib import Path

import buildozer.targets.android


source = Path(buildozer.targets.android.__file__)
contents = source.read_text()
anchor = "        # support for extra-manifest-application-arguments\n"
addition = """        # Application child elements (receivers and services)
        extra_application_xml = self.buildozer.config.get(
            'app', 'android.extra_manifest_application_xml', fallback='')
        if extra_application_xml:
            cmd.append('--extra-manifest-application-xml')
            cmd.append(open(extra_application_xml, 'rt').read())
"""

if contents.count(anchor) != 1:
    raise RuntimeError("Unsupported Buildozer version: manifest hook not found")
source.write_text(contents.replace(anchor, addition + anchor, 1))
print("Enabled Buildozer application XML support:", source)
