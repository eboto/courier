import Foundation
import SwiftyJSON

public struct RecordKey: Serializable {
    
    public let x: Int?
    
    public let y: Bool?
    
    public init(
        x: Int?,
        y: Bool?
    ) {
        self.x = x
        self.y = y
    }
    
    public static func readJSON(json: JSON) throws -> RecordKey {
        return RecordKey(
            x: json["x"].int,
            y: json["y"].bool
        )
    }
    public func writeData() -> [String: AnyObject] {
        var dict: [String : AnyObject] = [:]
        if let x = self.x {
            dict["x"] = x
        }
        if let y = self.y {
            dict["y"] = y
        }
        return dict
    }
}