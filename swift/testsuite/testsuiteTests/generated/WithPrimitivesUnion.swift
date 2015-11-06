import Foundation
import SwiftyJSON

public struct WithPrimitivesUnion: Serializable {
    
    public let union: Union?
    
    public init(
        union: Union?
    ) {
        self.union = union
    }
    
    public enum Union: Serializable {
        case IntMember(Int)
        case LongMember(Int)
        case FloatMember(Float)
        case DoubleMember(Double)
        case BooleanMember(Bool)
        case StringMember(String)
        case BytesMember(String)
        case UNKNOWN$([String : AnyObject])
        public static func readJSON(json: JSON) throws -> Union {
            let dict = json.dictionaryValue
            if let member = dict["int"] {
                return .IntMember(member.intValue)
            }
            if let member = dict["long"] {
                return .LongMember(member.intValue)
            }
            if let member = dict["float"] {
                return .FloatMember(member.floatValue)
            }
            if let member = dict["double"] {
                return .DoubleMember(member.doubleValue)
            }
            if let member = dict["boolean"] {
                return .BooleanMember(member.boolValue)
            }
            if let member = dict["string"] {
                return .StringMember(member.stringValue)
            }
            if let member = dict["bytes"] {
                return .BytesMember(member.stringValue)
            }
            if let unknownDict = json.dictionaryObject {
                return .UNKNOWN$(unknownDict)
            } else {
                throw ReadError.MalformedUnion
            }
        }
        public func writeData() -> [String: AnyObject] {
            switch self {
            case .IntMember(let member):
                return ["int": member];
            case .LongMember(let member):
                return ["long": member];
            case .FloatMember(let member):
                return ["float": member];
            case .DoubleMember(let member):
                return ["double": member];
            case .BooleanMember(let member):
                return ["boolean": member];
            case .StringMember(let member):
                return ["string": member];
            case .BytesMember(let member):
                return ["bytes": member];
            case .UNKNOWN$(let dict):
                return dict
            }
        }
    }
    
    public static func readJSON(json: JSON) throws -> WithPrimitivesUnion {
        return WithPrimitivesUnion(
            union: try json["union"].json.map { try Union.readJSON($0) }
        )
    }
    public func writeData() -> [String: AnyObject] {
        var dict: [String : AnyObject] = [:]
        if let union = self.union {
            dict["union"] = union.writeData()
        }
        return dict
    }
}
