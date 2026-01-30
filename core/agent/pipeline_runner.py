from core.pipelines.image_pipeline import process_image
from core.pipelines.identity_pipeline import process_username
from core.pipelines.infrastructure_pipeline import process_infrastructure

class PipelineRunner:

    def __init__(self, kg, face_matcher):
        self.kg = kg
        self.face_matcher = face_matcher

    def execute(self, primitive, node):
        """
        Executes OSINT primitive based on agent decision
        """

        if primitive == "image_fingerprint":
            return process_image(node.value, self.kg, self.face_matcher)

        if primitive == "identity_osint":
            return process_username(node, self.kg)
        
        if primitive == "infrastructure_osint":
            return process_infrastructure(node, self.kg)
